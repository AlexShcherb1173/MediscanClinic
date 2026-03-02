"""
Представления приложения записей на приём.
Содержит:
- calendar_view — рендер сетки месяца (partial для выбора даты);
- slots — выдача доступных слотов времени (partial для HTMX);
- appointment_create — создание записи с безопасной блокировкой слота в транзакции;
- appointment_success — страница успешной записи (должна быть защищена от доступа к чужим записям).
Также включает вспомогательные функции для:
- безопасного парсинга даты/целых чисел,
- автозаполнения имени и телефона пользователя по данным профиля/истории.
"""

from __future__ import annotations

import calendar
from datetime import date as dt_date
from datetime import datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

from .forms import AppointmentCreateForm
from .models import Appointment, AppointmentSlot
from .notifications import (AppointmentNotification, notify_email,
                            notify_telegram)


def appointments_index(request):
    """
    Индексный обработчик раздела записей.
    Выполняет простой редирект на страницу создания записи.
    """
    return redirect("appointments:create")


# ---------------- Helpers ----------------
def _safe_int(value: str | None) -> int | None:
    """
    Безопасно преобразует значение в int.
    Возвращает None, если:
    - значение пустое/None,
    - строка не является корректным целым числом.
    Параметры:
       value (str | None): Исходное значение (обычно из query params).
    Возвращает:
        int | None: Целое число или None.
    """
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_day(value: str | None) -> dt_date | None:
    """
    Безопасно парсит дату из строки формата YYYY-MM-DD.
    Параметры:
      value (str | None): Строка даты.
    Возвращает:
      date | None: Объект даты или None при некорректном формате/значении.
    """
    if not value:
        return None
    return parse_date(value)


def _first_day_with_slots(
    service_id: int | None, start_day: dt_date, days_ahead: int = 31
) -> dt_date | None:
    """
    Ищет ближайшую дату, начиная со start_day, где есть свободные активные слоты.
    Слот считается доступным, если:
     - is_active=True,
     - is_booked=False,
     - starts_at попадает в диапазон дат [start_day; start_day + days_ahead].
    Параметры:
        service_id (int | None): ID услуги для фильтрации (если None — по всем услугам).
        start_day (date): Дата, с которой начинается поиск.
        days_ahead (int): Горизонт поиска (по умолчанию 31 день).
    Возвращает:
        date | None: Дата первого найденного доступного слота или None, если слотов нет.
    """
    qs = AppointmentSlot.objects.filter(
        is_active=True,
        is_booked=False,
        starts_at__date__gte=start_day,
        starts_at__date__lte=start_day + timedelta(days=days_ahead),
    )
    if service_id:
        qs = qs.filter(service_id=service_id)
    return qs.order_by("starts_at").values_list("starts_at__date", flat=True).first()


def _user_full_name(user) -> str:
    """
    Пытается получить ФИО пользователя из разных источников.
    Стратегия:
        1) user.get_full_name()
        2) user.full_name
        3) связанные объекты profile/patient/person (full_name или fio)
        4) последняя запись Appointment.full_name для этого пользователя
        5) fallback: email или username
    Параметры:
        user: Пользователь Django (request.user).
    Возвращает:
        str: Найденное ФИО (или пустая строка, если пользователь анонимный/данных нет).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    try:
        full = (user.get_full_name() or "").strip()
        if full:
            return full
    except Exception:
        pass

    full = (getattr(user, "full_name", "") or "").strip()
    if full:
        return full

    for rel in ("profile", "patient", "person"):
        obj = getattr(user, rel, None)
        if obj is not None:
            full = (
                getattr(obj, "full_name", "") or getattr(obj, "fio", "") or ""
            ).strip()
            if full:
                return full

    last = (
        Appointment.objects.filter(user=user)
        .exclude(full_name__isnull=True)
        .exclude(full_name__exact="")
        .order_by("-created_at", "-id")
        .first()
    )
    if last:
        return (last.full_name or "").strip()

    email = (getattr(user, "email", "") or "").strip()
    if email:
        return email
    return (getattr(user, "username", "") or "").strip()


def _user_phone(user) -> str:
    """
    Пытается получить телефон пользователя из профиля/связанных объектов или истории записей.
    Стратегия:
        1) user.phone
        2) связанные объекты profile/patient/person.phone
        3) последняя запись Appointment.phone для этого пользователя
    Параметры:
        user: Пользователь Django (request.user).
    Возвращает:
        str: Найденный номер телефона (или пустая строка, если пользователь анонимный/данных нет).
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    phone = (getattr(user, "phone", "") or "").strip()
    if phone:
        return phone

    for rel in ("profile", "patient", "person"):
        obj = getattr(user, rel, None)
        if obj is not None:
            phone = (getattr(obj, "phone", "") or "").strip()
            if phone:
                return phone

    last = (
        Appointment.objects.filter(user=user)
        .exclude(phone__isnull=True)
        .exclude(phone__exact="")
        .order_by("-created_at", "-id")
        .first()
    )
    if last:
        return (last.phone or "").strip()

    return ""


@require_GET
def calendar_view(request):
    """
    Рендерит partial с сеткой месяца для выбора даты записи.
    Query-параметры:
        m: отображаемый месяц в формате "YYYY-MM" (опционально).
        preferred_date / date: выбранная дата в формате "YYYY-MM-DD" (опционально).
    Правила:
        - если выбранная дата некорректна или в прошлом — принудительно используется today;
        - переход в прошлые месяцы запрещён (prev_disabled=True).
    Возвращает:
        HTML partial "appointments/_calendar_month.html" с данными:
        today, selected, year, month, blanks, days, prev_m, next_m, prev_disabled.
    """
    today = timezone.localdate()

    m = request.GET.get("m")  # "2026-02"
    selected_raw = request.GET.get("preferred_date") or request.GET.get("date") or ""
    selected_date = _safe_day(selected_raw)

    # ✅ если пришла прошедшая дата — принудительно ставим today
    if not selected_date or selected_date < today:
        selected_date = today

    # определяем первый день отображаемого месяца
    if m:
        try:
            year, month = map(int, m.split("-"))
            first = dt_date(year, month, 1)
        except Exception:
            first = dt_date(selected_date.year, selected_date.month, 1)
    else:
        first = dt_date(selected_date.year, selected_date.month, 1)

    year, month = first.year, first.month
    _, days_in_month = calendar.monthrange(year, month)
    first_weekday = first.weekday()

    blanks = list(range(first_weekday))
    days = [dt_date(year, month, d) for d in range(1, days_in_month + 1)]

    prev_month = (first.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    # ✅ запрещаем уход в прошлые месяцы
    min_month = today.replace(day=1)
    prev_disabled = prev_month < min_month

    return render(
        request,
        "appointments/_calendar_month.html",
        {
            "today": today,
            "selected": selected_date.strftime("%Y-%m-%d"),
            "year": year,
            "month": month,
            "blanks": blanks,
            "days": days,
            "prev_m": prev_month.strftime("%Y-%m"),
            "next_m": next_month.strftime("%Y-%m"),
            "prev_disabled": prev_disabled,
        },
    )


@require_GET
def slots(request):
    """
    Возвращает partial со списком доступных слотов времени (HTMX).
    Назначение:
        Отрисовать плитки времени для выбранных:
        - услуги (service_id),
        - даты (preferred_date/date),
          при условии, что пациент ввёл минимально необходимые данные (ФИО + телефон).
    Требует (логически):
        - заполненные данные пациента (full_name + phone),
        - выбранную услугу,
        - выбранную дату (не в прошлом).
    Поведение:
        - если пациент не готов / услуга не выбрана / дата не выбрана — возвращает пустой список слотов
          с соответствующими флагами состояния для UI;
        - если дата в прошлом — возвращает флаг date_in_past=True и пустой список;
        - иначе выбирает активные и свободные слоты по дню и услуге и возвращает их в формате:
          [{"id": "<pk>", "label": "HH:MM"}, ...].
    Возвращает:
        HTML partial "appointments/_slots_tiles.html".
    """
    service_id_raw = (
        request.GET.get("service")
        or request.GET.get("service_id")
        or request.GET.get("service-select")
        or ""
    )
    service_id = _safe_int(service_id_raw)

    date_str = (
        request.GET.get("preferred_date") or request.GET.get("date") or ""
    ).strip()
    day = parse_date(date_str) if date_str else None

    full_name = (
        request.GET.get("full_name") or request.GET.get("id_full_name") or ""
    ).strip()
    phone = (request.GET.get("phone") or request.GET.get("id_phone") or "").strip()
    patient_ready = (len(full_name) >= 3) and (len(phone) >= 6)

    service_selected = bool(service_id)
    date_selected = day is not None

    # ✅ запрет прошлого на сервере (если кто-то подставит вручную)
    today = timezone.localdate()
    date_in_past = bool(day) and (day < today)

    if not patient_ready:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": False,
                "service_selected": False,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    if not service_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": False,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    if not date_selected:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": True,
                "date_selected": False,
                "date_in_past": False,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    # если дата выбрана, но в прошлом
    if date_in_past:
        return render(
            request,
            "appointments/_slots_tiles.html",
            {
                "patient_ready": True,
                "service_selected": True,
                "date_selected": True,
                "date_in_past": True,
                "slot_items": [],
                "selected_slot_id": "",
            },
        )

    tz = timezone.get_current_timezone()
    start_local = timezone.make_aware(datetime.combine(day, time.min), tz)
    end_local = timezone.make_aware(datetime.combine(day, time.max), tz)

    qs = AppointmentSlot.objects.filter(
        is_active=True,
        is_booked=False,
        starts_at__gte=start_local,
        starts_at__lte=end_local,
        service_id=service_id,
    ).order_by("starts_at")

    slot_items = [
        {
            "id": str(slot.pk),
            "label": timezone.localtime(slot.starts_at, tz).strftime("%H:%M"),
        }
        for slot in qs
    ]

    selected_slot_id = (
        request.GET.get("slot")
        or request.GET.get("selected_slot")
        or request.GET.get("slot_id")
        or ""
    )

    return render(
        request,
        "appointments/_slots_tiles.html",
        {
            "patient_ready": True,
            "service_selected": True,
            "date_selected": True,
            "date_in_past": False,
            "slot_items": slot_items,
            "selected_slot_id": str(selected_slot_id),
        },
    )


def appointment_create(request):
    """
    Создаёт запись на приём (GET — форма, POST — создание записи).
    Поддерживает "блокировку" полей через query params:
        service=<id>  — предвыбрать услугу и (опционально) скрыть/зафиксировать поле;
        doctor=<id>   — предвыбрать врача и (опционально) скрыть/зафиксировать поле;
        promo=<slug>  — ограничить список услуг услугами акции (promo.services).
    Гарантия от двойного бронирования:
        Используется транзакция + select_for_update() на строке слота:
        - лочим слот,
        - проверяем is_active и is_booked,
        - помечаем слот занятым,
        - создаём Appointment, привязывая slot/service/doctor/promo,
        - сохраняем запись.
    После успешного создания:
        - отправляет уведомления в клинику (email + Telegram),
        - очищает черновик из session,
        - сохраняет last_appointment_pk в session для доступа анонимного пользователя к success-странице,
        - делает редирект на appointments:success.
    Ошибки:
        - при конфликте бронирования (IntegrityError/DoesNotExist) добавляет ошибку в поле slot
          и повторно рендерит форму.
    """
    service_id = request.GET.get("service")
    doctor_id = request.GET.get("doctor")
    promo_slug = request.GET.get("promo")

    locked_service = bool(service_id)
    locked_doctor = bool(doctor_id)

    promo = None
    promo_services_qs = None

    if promo_slug:
        promo = get_object_or_404(Promo, slug=promo_slug, is_active=True)
        promo_services_qs = promo.services.filter(
            is_active=True, category__is_active=True
        )

        if not service_id and promo_services_qs.count() == 1:
            service_id = str(promo_services_qs.first().id)
            locked_service = True

    service = (
        get_object_or_404(
            Service, id=service_id, is_active=True, category__is_active=True
        )
        if service_id
        else None
    )
    doctor = (
        get_object_or_404(Doctor, id=doctor_id, is_active=True) if doctor_id else None
    )

    draft = request.session.get("appointment_draft", {}) or {}

    base_ctx = {
        "service": service,
        "doctor": doctor,
        "promo": promo,
        "locked_service": locked_service,
        "locked_doctor": locked_doctor,
    }

    if request.method == "POST":
        form = AppointmentCreateForm(
            request.POST,
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=(
                promo_services_qs if promo_services_qs is not None else None
            ),
        )

        if form.is_valid():
            slot_obj: AppointmentSlot = form.cleaned_data["slot"]

            try:
                with transaction.atomic():
                    slot_locked = AppointmentSlot.objects.select_for_update().get(
                        pk=slot_obj.pk
                    )
                    slot_day = timezone.localtime(slot_obj.starts_at).date()
                    if slot_day < timezone.localdate():
                        form.add_error("slot", "Нельзя записаться на прошедшую дату.")
                        return render(
                            request,
                            "appointments/create.html",
                            {**base_ctx, "form": form},
                        )

                    if (not slot_locked.is_active) or slot_locked.is_booked:
                        form.add_error("slot", "Этот слот уже занят. Выберите другой.")
                        return render(
                            request,
                            "appointments/create.html",
                            {**base_ctx, "form": form},
                        )

                    slot_locked.is_booked = True
                    slot_locked.save(update_fields=["is_booked"])

                    appointment: Appointment = form.save(commit=False)
                    appointment.user = (
                        request.user if request.user.is_authenticated else None
                    )

                    appointment.slot = slot_locked
                    appointment.service = slot_locked.service
                    appointment.doctor = doctor
                    appointment.promo = promo
                    appointment.preferred_datetime = slot_locked.starts_at
                    appointment.save()

            except (IntegrityError, AppointmentSlot.DoesNotExist):
                form.add_error("slot", "Этот слот уже занят. Выберите другой.")
                return render(
                    request, "appointments/create.html", {**base_ctx, "form": form}
                )

            payload = AppointmentNotification(
                full_name=appointment.full_name,
                phone=appointment.phone,
                service_name=appointment.service.name if appointment.service else "",
                preferred_datetime_iso=(
                    appointment.preferred_datetime.isoformat()
                    if appointment.preferred_datetime
                    else ""
                ),
            )
            notify_email(payload)
            notify_telegram(payload)

            request.session.pop("appointment_draft", None)
            request.session["last_appointment_pk"] = appointment.pk
            request.session.save()

            return redirect("appointments:success", pk=appointment.pk)

    else:
        user_full_name = _user_full_name(request.user)
        user_phone = _user_phone(request.user)
        user_email = (
            (getattr(request.user, "email", "") or "").strip()
            if request.user.is_authenticated
            else ""
        )

        initial = {
            "full_name": draft.get("full_name") or user_full_name or "",
            "phone": draft.get("phone") or user_phone or "",
            "email": draft.get("email") or user_email or "",
            "comment": draft.get("comment", ""),
        }

        if service:
            init_day = _safe_day(draft.get("preferred_date")) or timezone.localdate()
            nearest = _first_day_with_slots(service.id, init_day, days_ahead=31)
            if nearest:
                init_day = nearest
            initial["preferred_date"] = init_day

        form = AppointmentCreateForm(
            service_id=service.id if service else None,
            doctor_id=doctor.id if doctor else None,
            lock_service=locked_service,
            lock_doctor=locked_doctor,
            service_queryset=(
                promo_services_qs if promo_services_qs is not None else None
            ),
            initial=initial,
        )

    return render(request, "appointments/create.html", {**base_ctx, "form": form})


def appointment_success(request, pk: int):
    """
    Отображает страницу успешной записи.
    Защита доступа:
        - авторизованный пользователь видит только свои записи (appointment.user_id == request.user.id);
        - анонимный пользователь видит только последнюю запись, созданную в текущей сессии
          (session["last_appointment_pk"] == pk).
    При нарушении доступа:
        - редирект на страницу создания записи.
    Возвращает:
        HTML-страницу "appointments/success.html" с объектом appointment.
    """
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user.is_authenticated:
        if appointment.user_id != request.user.id:
            return redirect("appointments:create")
    else:
        if request.session.get("last_appointment_pk") != appointment.pk:
            return redirect("appointments:create")

    return render(request, "appointments/success.html", {"appointment": appointment})
