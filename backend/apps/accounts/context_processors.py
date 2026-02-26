# apps/accounts/context_processors.py
from __future__ import annotations

from typing import Any

from apps.appointments.models import Appointment


def _user_full_name(user) -> str:
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    # 1) стандартный Django
    try:
        full = (user.get_full_name() or "").strip()
        if full:
            return full
    except Exception:
        pass

    # 2) кастомное поле user.full_name
    full = (getattr(user, "full_name", "") or "").strip()
    if full:
        return full

    # 3) profile/patient/person
    for rel in ("profile", "patient", "person"):
        obj = getattr(user, rel, None)
        if obj is not None:
            full = (getattr(obj, "full_name", "") or getattr(obj, "fio", "") or "").strip()
            if full:
                return full

    # 4) fallback: последняя запись
    last = (
        Appointment.objects
        .filter(user=user)
        .exclude(full_name__isnull=True)
        .exclude(full_name__exact="")
        .order_by("-id")  # если есть created_at — можно заменить на "-created_at"
        .first()
    )
    if last:
        return (last.full_name or "").strip()

    # fallback: email/username
    email = (getattr(user, "email", "") or "").strip()
    if email:
        return email
    return (getattr(user, "username", "") or "").strip()


def _user_phone(user) -> str:
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
        Appointment.objects
        .filter(user=user)
        .exclude(phone__isnull=True)
        .exclude(phone__exact="")
        .order_by("-id")
        .first()
    )
    if last:
        return (last.phone or "").strip()

    return ""


def lk_user_data(request) -> dict[str, Any]:
    """
    Данные для ЛК (ФИО/телефон). Работает даже если в User нет first/last name.
    """
    user = getattr(request, "user", None)
    return {
        "lk_full_name": _user_full_name(user),
        "lk_phone": _user_phone(user),
    }