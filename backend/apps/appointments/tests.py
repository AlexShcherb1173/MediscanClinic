from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.appointments.emailing import send_reminder_email
from apps.appointments.forms import AppointmentCreateForm
from apps.appointments.models import Appointment, AppointmentSlot
from apps.appointments.tasks import (normalize_emails,
                                     normalize_phone_for_smsru, smsru_send)
from apps.appointments.telegram_client import send_telegram_message
from apps.appointments.utils import get_busy_time_labels
from apps.services.models import Service, ServiceCategory


class AppointmentsBaseMixin:
    def create_category(self, *, name: str | None = None, **kwargs) -> ServiceCategory:
        """
        Helper: create an active service category for tests.
        """
        suffix = uuid4().hex[:8]
        return ServiceCategory.objects.create(
            name=name or f"Cat {suffix}",
            slug=kwargs.pop("slug", f"cat-{suffix}"),
            is_active=True,
            **kwargs,
        )

    def create_service(
        self,
        *,
        name: str | None = None,
        category: ServiceCategory | None = None,
        price_from: str = "1000.00",
        **kwargs,
    ) -> Service:
        """
        Helper: create an active service with guaranteed-unique slug for tests.
        """
        if category is None:
            category = self.create_category()

        suffix = uuid4().hex[:8]
        return Service.objects.create(
            category=category,
            name=name or f"Service {suffix}",
            slug=kwargs.pop("slug", f"svc-{suffix}"),
            price_from=Decimal(price_from),
            is_active=True,
            **kwargs,
        )

    def create_slot(
        self,
        service: Service,
        starts_at,
        ends_at=None,
        is_active: bool = True,
        is_booked: bool = False,
    ) -> AppointmentSlot:
        ends_at = ends_at or (starts_at + timedelta(minutes=20))
        return AppointmentSlot.objects.create(
            service=service,
            starts_at=starts_at,
            ends_at=ends_at,
            is_active=is_active,
            is_booked=is_booked,
        )


class AppointmentModelsTests(AppointmentsBaseMixin, TestCase):
    def test_appointment_slot_str(self):
        service = self.create_service()
        starts = timezone.now() + timedelta(days=1)
        slot = self.create_slot(service, starts)
        s = str(slot)
        self.assertIn(service.name, s)
        self.assertIn(starts.strftime("%d.%m"), s)

    def test_appointment_clean_requires_slot(self):
        """
        По бизнес-логике Appointment без slot не существует.
        """
        appt = Appointment(
            service=None,
            slot=None,
            doctor=None,
            promo=None,
            user=None,
            full_name="Иван Иванов",
            phone="+79990000000",
            email="",
            comment="",
            preferred_datetime=None,
        )
        with self.assertRaises(ValidationError):
            appt.full_clean()

    def test_unique_appointment_slot_constraint(self):
        service = self.create_service()
        starts = timezone.now() + timedelta(days=1)
        slot = self.create_slot(service, starts)

        a1 = Appointment.objects.create(
            service=service,
            slot=slot,
            doctor=None,
            promo=None,
            user=None,
            full_name="П1",
            phone="+79990000001",
            email="",
            comment="",
            preferred_datetime=starts,
            status=Appointment.Status.NEW,
        )
        self.assertIsNotNone(a1.pk)

        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                service=service,
                slot=slot,
                doctor=None,
                promo=None,
                user=None,
                full_name="П2",
                phone="+79990000002",
                email="",
                comment="",
                preferred_datetime=starts,
                status=Appointment.Status.NEW,
            )


class AppointmentFormTests(AppointmentsBaseMixin, TestCase):
    def test_form_slot_queryset_filtered_by_service_and_date(self):
        service = self.create_service()
        other_service = self.create_service(
            name="Рентген", category=service.category, price_from="1200.00"
        )

        day = timezone.localdate() + timedelta(days=2)
        tz = timezone.get_current_timezone()

        slot_ok = self.create_slot(
            service,
            timezone.make_aware(
                timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                    hour=10, minute=0
                ),
                tz,
            ),
        )
        self.create_slot(
            other_service,
            timezone.make_aware(
                timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                    hour=10, minute=20
                ),
                tz,
            ),
        )

        form = AppointmentCreateForm(
            data={},
            service_id=service.id,
            initial={"preferred_date": day},
        )
        qs = form.fields["slot"].queryset
        self.assertIn(slot_ok, list(qs))
        self.assertTrue(all(s.service_id == service.id for s in qs))

    def test_clean_slot_rejects_inactive(self):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=11, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, starts, is_active=False, is_booked=False)

        form = AppointmentCreateForm(
            data={
                "service": service.id,
                "doctor": "",
                "full_name": "Тест",
                "phone": "+79990000000",
                "email": "",
                "comment": "",
                "preferred_date": str(day),
                "slot": slot.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("slot", form.errors)

    def test_clean_slot_rejects_booked(self):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=11, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, starts, is_active=True, is_booked=True)

        form = AppointmentCreateForm(
            data={
                "service": service.id,
                "doctor": "",
                "full_name": "Тест",
                "phone": "+79990000000",
                "email": "",
                "comment": "",
                "preferred_date": str(day),
                "slot": slot.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("slot", form.errors)

    def test_clean_slot_rejects_past(self):
        service = self.create_service()
        starts = timezone.now() - timedelta(hours=2)
        slot = self.create_slot(service, starts, is_active=True, is_booked=False)

        form = AppointmentCreateForm(
            data={
                "service": service.id,
                "doctor": "",
                "full_name": "Тест",
                "phone": "+79990000000",
                "email": "",
                "comment": "",
                "preferred_date": str(timezone.localdate()),
                "slot": slot.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("slot", form.errors)

    def test_clean_slot_rejects_wrong_service(self):
        cat = self.create_category()
        s1 = self.create_service(name="S1", category=cat, price_from="1000.00")
        s2 = self.create_service(name="S2", category=cat, price_from="1200.00")

        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=12, minute=0
            ),
            tz,
        )
        slot_s2 = self.create_slot(s2, starts)

        form = AppointmentCreateForm(
            data={
                "service": s1.id,
                "doctor": "",
                "full_name": "Тест",
                "phone": "+79990000000",
                "email": "",
                "comment": "",
                "preferred_date": str(day),
                "slot": slot_s2.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("slot", form.errors)


class AppointmentViewsTests(AppointmentsBaseMixin, TestCase):
    def test_slots_requires_patient_ready(self):
        url = reverse("appointments:slots")
        r = self.client.get(url, {"service": "", "preferred_date": ""})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context["patient_ready"])

    def test_slots_requires_service(self):
        url = reverse("appointments:slots")
        day = str(timezone.localdate() + timedelta(days=1))
        r = self.client.get(
            url, {"full_name": "Анна", "phone": "+79990000000", "preferred_date": day}
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["patient_ready"])
        self.assertFalse(r.context["service_selected"])

    def test_slots_requires_date(self):
        url = reverse("appointments:slots")
        service = self.create_service()

        # preferred_date отсутствует
        r = self.client.get(
            url, {"full_name": "Анна", "phone": "+79990000000", "service": service.id}
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["patient_ready"])
        self.assertTrue(r.context["service_selected"])
        self.assertFalse(r.context["date_selected"])

        # preferred_date пустая строка
        r2 = self.client.get(
            url,
            {
                "full_name": "Анна",
                "phone": "+79990000000",
                "service": service.id,
                "preferred_date": "",
            },
        )
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(r2.context["date_selected"])

    def test_slots_returns_items(self):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=10, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, starts)

        url = reverse("appointments:slots")
        r = self.client.get(
            url,
            {
                "full_name": "Анна",
                "phone": "+79990000000",
                "service": service.id,
                "preferred_date": str(day),
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["patient_ready"])
        self.assertTrue(r.context["service_selected"])
        self.assertTrue(r.context["date_selected"])
        items = r.context["slot_items"]
        self.assertTrue(any(x["id"] == str(slot.id) for x in items))

    def test_calendar_view_ok(self):
        url = reverse("appointments:calendar")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("selected", r.context)

    @patch("apps.appointments.views.notify_email")
    @patch("apps.appointments.views.notify_telegram")
    def test_appointment_create_post_books_slot_and_creates_appointment(
        self, m_tg, m_email
    ):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=13, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, starts, is_active=True, is_booked=False)

        url = reverse("appointments:create") + f"?service={service.id}"
        payload = {
            "doctor": "",
            "full_name": "Пётр",
            "phone": "+79990000000",
            "email": "p@test.com",
            "comment": "ok",
            "preferred_date": str(day),
            "slot": str(slot.id),
        }

        r = self.client.post(url, data=payload)
        self.assertEqual(r.status_code, 302)

        slot.refresh_from_db()
        self.assertTrue(slot.is_booked)

        appt = Appointment.objects.get(slot=slot)
        self.assertEqual(appt.full_name, "Пётр")
        self.assertEqual(appt.service_id, service.id)
        self.assertEqual(appt.preferred_datetime, slot.starts_at)

        self.assertTrue(m_email.called)
        self.assertTrue(m_tg.called)

    @patch("apps.appointments.views.notify_email")
    @patch("apps.appointments.views.notify_telegram")
    def test_appointment_create_double_booking_shows_error(self, m_tg, m_email):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()
        starts = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=14, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, starts, is_active=True, is_booked=False)

        url = reverse("appointments:create") + f"?service={service.id}"
        payload = {
            "doctor": "",
            "full_name": "П1",
            "phone": "+79990000000",
            "email": "p1@test.com",
            "comment": "",
            "preferred_date": str(day),
            "slot": str(slot.id),
        }

        r1 = self.client.post(url, data=payload)
        self.assertEqual(r1.status_code, 302)

        payload["full_name"] = "П2"
        payload["email"] = "p2@test.com"
        r2 = self.client.post(url, data=payload)
        self.assertEqual(r2.status_code, 200)

        # важно: сообщение должно совпадать с твоим clean_slot()
        self.assertContains(r2, "Этот слот уже занят. Выберите другой.", html=False)


class AppointmentUtilsAndServicesTests(AppointmentsBaseMixin, TestCase):
    def test_get_busy_time_labels(self):
        service = self.create_service()
        day = timezone.localdate() + timedelta(days=1)
        tz = timezone.get_current_timezone()

        dt1 = timezone.make_aware(
            timezone.datetime.combine(day, timezone.datetime.min.time()).replace(
                hour=9, minute=0
            ),
            tz,
        )
        slot = self.create_slot(service, dt1)
        Appointment.objects.create(
            service=service,
            slot=slot,
            full_name="Busy",
            phone="+79990000000",
            email="",
            comment="",
            preferred_datetime=dt1,
            status=Appointment.Status.NEW,
        )

        labels = get_busy_time_labels(service.id, day)
        self.assertIn("09:00", labels)

    @override_settings(DEFAULT_FROM_EMAIL="clinic@test.com")
    @patch("apps.appointments.emailing.send_mail")
    def test_send_reminder_email_no_email_no_send(self, m_send_mail):
        service = self.create_service()
        dt = timezone.now() + timedelta(days=1)
        slot = self.create_slot(service, dt)
        appt = Appointment.objects.create(
            service=service,
            slot=slot,
            full_name="X",
            phone="+79990000000",
            email="",
            comment="",
            preferred_datetime=dt,
            status=Appointment.Status.NEW,
        )
        send_reminder_email(appt, "24h")
        m_send_mail.assert_not_called()

    @override_settings(DEFAULT_FROM_EMAIL="clinic@test.com")
    @patch("apps.appointments.emailing.send_mail")
    def test_send_reminder_email_sends(self, m_send_mail):
        service = self.create_service()
        dt = timezone.now() + timedelta(days=1)
        slot = self.create_slot(service, dt)
        appt = Appointment.objects.create(
            service=service,
            slot=slot,
            full_name="X",
            phone="+79990000000",
            email="x@test.com",
            comment="",
            preferred_datetime=dt,
            status=Appointment.Status.NEW,
        )
        send_reminder_email(appt, "2h")
        m_send_mail.assert_called_once()

    @patch("apps.appointments.telegram_client.requests.post")
    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    def test_send_telegram_message_no_config(self, m_post):
        send_telegram_message("hi")
        m_post.assert_not_called()

    def test_normalize_emails(self):
        self.assertEqual(normalize_emails("a@b.com"), ["a@b.com"])
        self.assertEqual(normalize_emails(["a@b.com", " "]), ["a@b.com"])
        self.assertEqual(
            normalize_emails("['a@b.com', 'c@d.com']"), ["a@b.com", "c@d.com"]
        )
        self.assertEqual(normalize_emails(("x@y.com",)), ["x@y.com"])
        self.assertEqual(normalize_emails(""), [])

    def test_normalize_phone_for_smsru(self):
        self.assertEqual(normalize_phone_for_smsru("+7 (999) 000-00-00"), "79990000000")
        self.assertEqual(normalize_phone_for_smsru("8 999 000 00 00"), "79990000000")

    @override_settings(SMS_RU_API_ID="")
    def test_smsru_send_without_api_id(self):
        ok, info = smsru_send("+79990000000", "Hi")
        self.assertFalse(ok)
        self.assertIn("SMS_RU_API_ID", info)


# ----------------------
# Phone validation tests (E.164) with required business fields (slot)
# ----------------------


class AppointmentPhoneValidationTests(AppointmentsBaseMixin, TestCase):
    def setUp(self):
        self.service = self.create_service()
        dt = timezone.now() + timedelta(days=1)
        self.slot = self.create_slot(self.service, dt)

    def test_invalid_phone_rejected(self):
        a = Appointment(full_name="Test", phone="12334455667788899")
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_valid_phone_e164_passes(self):
        a = Appointment(full_name="Test", phone="+79991234567")
        # но appointment без slot существовать не может — создадим минимальные service+slot
        cat = ServiceCategory.objects.create(
            name="Diag", slug="diag", order=1, is_active=True
        )
        svc = Service.objects.create(
            category=cat,
            name="UZI",
            slug="uzi",
            price_from=Decimal("1000.00"),
            is_active=True,
        )
        now = timezone.now()
        slot = AppointmentSlot.objects.create(
            service=svc,
            starts_at=now + timezone.timedelta(days=1),
            ends_at=now + timezone.timedelta(days=1, minutes=20),
            is_active=True,
            is_booked=False,
        )
        a.service = svc
        a.slot = slot

        a.full_clean()  # не должно падать
        self.assertEqual(a.phone, "+79991234567")
        a.full_clean()
        self.assertEqual(a.phone, "+79991234567")


class AppointmentPhoneModelTests(TestCase):
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name="Диагностика",
            slug="diag",
            order=1,
            is_active=True,
        )
        self.service = Service.objects.create(
            category=self.category,
            name="УЗИ",
            slug="uzi",
            price_from=Decimal("1000.00"),
            is_active=True,
        )

        def test_phone_e164_is_accepted_on_full_clean(self):
            a = Appointment(
                full_name="Test",
                phone="+79991234567",
                service=self.service,
                slot=self.slot,
            )
            a.full_clean()
            self.assertEqual(a.phone, "+79991234567")

        now = timezone.now()
        self.slot = AppointmentSlot.objects.create(
            service=self.service,
            starts_at=now + timezone.timedelta(days=1),
            ends_at=now + timezone.timedelta(days=1, minutes=30),
            is_active=True,
            is_booked=False,
        )


class AppointmentPhoneFormTests(AppointmentsBaseMixin, TestCase):
    def setUp(self):
        self.service = self.create_service(name="УЗИ", slug=f"uzi-{uuid4().hex[:8]}")
        now = timezone.now()
        self.slot = self.create_slot(self.service, now + timedelta(days=1))
        self.preferred_date = (now + timedelta(days=1)).date().isoformat()

    def test_form_normalizes_phone(self):
        form = AppointmentCreateForm(
            data={
                "service": self.service.id,
                "doctor": "",
                "full_name": "qwerty",
                "phone": "8 (999) 123-45-67",
                "email": "",
                "comment": "",
                "preferred_date": self.preferred_date,
                "slot": self.slot.id,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        # Важно: cleaned_data["phone"] зависит от того, где ты делаешь normalize_phone (форма или модель).
        # Если нормализуешь на модели (full_clean), то в форме может остаться "сырой" телефон.
        # Поэтому фиксируем через instance.full_clean().
        a = form.save(commit=False)
        a.full_clean()
        self.assertEqual(a.phone, "+79991234567")

    def test_form_rejects_invalid_phone(self):
        form = AppointmentCreateForm(
            data={
                "service": self.service.id,
                "doctor": "",
                "full_name": "qwerty",
                "phone": "12334455667788899",
                "email": "",
                "comment": "",
                "preferred_date": self.preferred_date,
                "slot": self.slot.id,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_form_accepts_e164_phone(self):
        form = AppointmentCreateForm(
            data={
                "service": self.service.id,
                "doctor": "",
                "full_name": "qwerty",
                "phone": "+79991234567",
                "email": "",
                "comment": "",
                "preferred_date": self.preferred_date,
                "slot": self.slot.id,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "+79991234567")
