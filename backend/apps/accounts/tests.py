from __future__ import annotations

from apps.accounts.backends import PhoneBackend
from apps.accounts.contact_utils import normalize_phone_or_email
from apps.accounts.forms import LoginForm, RegisterForm
from apps.accounts.utils import normalize_phone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class AccountsUtilsTests(TestCase):
    def test_normalize_phone_e164(self):
        self.assertEqual(normalize_phone("+7(985) 698-72-82"), "+79856987282")
        self.assertEqual(normalize_phone("8 985 698-72-82"), "+79856987282")
        with self.assertRaises(ValidationError):
            normalize_phone("")


class AccountsUserManagerTests(TestCase):
    def test_create_user_requires_phone(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(phone="", password="123456")

    def test_create_user_normalizes_phone_and_saves(self):
        u = User.objects.create_user(
            phone="+7(999) 000-00-00",
            password="123456",
            full_name="Иван Иванов",
            email="a@b.com",
        )
        self.assertEqual(u.phone, "+79990000000")
        self.assertTrue(u.check_password("123456"))

    def test_create_superuser_sets_flags(self):
        su = User.objects.create_superuser(
            phone="79990000011",
            password="123456",
            full_name="Админ",
        )
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_active)
        self.assertEqual(su.phone, "+79990000011")


class AccountsUserModelTests(TestCase):
    def test_user_str(self):
        u = User.objects.create_user(
            phone="79990000022", password="123456", full_name="Пользователь"
        )
        self.assertEqual(str(u), "Пользователь")

        u2 = User.objects.create_user(phone="79990000033", password="123456", full_name="")
        self.assertEqual(str(u2), "+79990000033")

    def test_touch_updates_last_seen(self):
        u = User.objects.create_user(phone="79990000044", password="123456", full_name="X")
        self.assertIsNone(u.last_seen_at)
        u.touch()
        u.refresh_from_db()
        self.assertIsNotNone(u.last_seen_at)
        self.assertLessEqual(u.last_seen_at, timezone.now())


class AccountsBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="79990000055",
            password="123456",
            full_name="Test User",
        )
        self.backend = PhoneBackend()

    def test_authenticate_by_username_phone(self):
        u = self.backend.authenticate(None, username="7 999 000-00-55", password="123456")
        self.assertIsNotNone(u)
        self.assertEqual(u.pk, self.user.pk)

    def test_authenticate_by_phone_kwarg(self):
        u = self.backend.authenticate(None, phone="+7(999)000-00-55", password="123456")
        self.assertIsNotNone(u)
        self.assertEqual(u.pk, self.user.pk)

    def test_authenticate_wrong_password(self):
        u = self.backend.authenticate(None, username="79990000055", password="wrong")
        self.assertIsNone(u)

    def test_authenticate_no_password(self):
        u = self.backend.authenticate(None, username="79990000055", password=None)
        self.assertIsNone(u)

    def test_authenticate_no_phone(self):
        u = self.backend.authenticate(None, username=None, phone=None, password="123456")
        self.assertIsNone(u)


class AccountsFormsTests(TestCase):
    def test_register_form_success(self):
        form = RegisterForm(
            data={
                "full_name": "Иван Иванов",
                "phone": "+7(999) 111-11-11",
                "email": "test@example.com",
                "password1": "123456",
                "password2": "123456",
            }
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.phone, "+79991111111")
        self.assertTrue(user.check_password("123456"))

    def test_register_form_password_mismatch(self):
        form = RegisterForm(
            data={
                "full_name": "Иван Иванов",
                "phone": "79991111112",
                "email": "",
                "password1": "123456",
                "password2": "654321",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_register_form_phone_already_exists(self):
        User.objects.create_user(phone="79991111113", password="123456", full_name="X")
        form = RegisterForm(
            data={
                "full_name": "Иван Иванов",
                "phone": "7 999 111-11-13",
                "email": "",
                "password1": "123456",
                "password2": "123456",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_login_form_success(self):
        User.objects.create_user(phone="79992223344", password="123456", full_name="X")
        form = LoginForm(data={"phone": "+7(999)222-33-44", "password": "123456"})
        self.assertTrue(form.is_valid())
        self.assertIn("user", form.cleaned_data)
        self.assertEqual(form.cleaned_data["phone"], "+79992223344")

    def test_login_form_invalid_credentials(self):
        User.objects.create_user(phone="79993334455", password="123456", full_name="X")
        form = LoginForm(data={"phone": "79993334455", "password": "wrong"})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class AccountsViewsTests(TestCase):
    def test_register_view_creates_user_and_logs_in(self):
        url = reverse("accounts:register")
        r = self.client.post(
            url,
            data={
                "full_name": "Иван Иванов",
                "phone": "+7(999) 555-55-55",
                "email": "x@y.com",
                "password1": "123456",
                "password2": "123456",
            },
            follow=False,
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(phone="+79995555555").exists())

    def test_login_view_logs_in(self):
        User.objects.create_user(phone="79996667788", password="123456", full_name="X")

        url = reverse("accounts:login")
        r = self.client.post(
            url,
            data={"phone": "7 999 666-77-88", "password": "123456"},
            follow=False,
        )
        self.assertEqual(r.status_code, 302)

    def test_logout_view(self):
        user = User.objects.create_user(phone="79990001122", password="123456", full_name="X")
        self.client.force_login(user)

        url = reverse("accounts:logout")
        r = self.client.get(url, follow=False)
        self.assertEqual(r.status_code, 302)


class ContactUtilsTests(TestCase):
    def test_accepts_email(self):
        r = normalize_phone_or_email("TeSt@Example.com")
        self.assertEqual(r.kind, "email")
        self.assertEqual(r.value, "test@example.com")

    def test_accepts_phone(self):
        r = normalize_phone_or_email("8 (999) 123-45-67")
        self.assertEqual(r.kind, "phone")
        self.assertEqual(r.value, "+79991234567")

    def test_rejects_garbage(self):
        with self.assertRaises(ValidationError):
            normalize_phone_or_email("qwerty")
