"""
Контекстные процессоры для приложения accounts.

Добавляет в контекст шаблонов данные для личного кабинета:
- lk_full_name — ФИО пользователя
- lk_phone — телефон пользователя

Предусмотрены резервные источники:
- связанные объекты profile / patient / person
- последняя запись Appointment
"""

from __future__ import annotations

from typing import Any

from apps.appointments.models import Appointment


def _user_full_name(user) -> str:
    """
    Определяет ФИО пользователя с использованием нескольких источников.
    Порядок поиска:
        1. user.get_full_name()
        2. user.full_name
        3. связанные объекты profile / patient / person
        4. последняя запись Appointment
        5. email
        6. username
    Возвращает:
        Строку с ФИО или доступным идентификатором,
        либо пустую строку, если пользователь не аутентифицирован.
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
            full = (getattr(obj, "full_name", "") or getattr(obj, "fio", "") or "").strip()
            if full:
                return full

    last = (
        Appointment.objects.filter(user=user)
        .exclude(full_name__isnull=True)
        .exclude(full_name__exact="")
        .order_by("-id")
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
    Определяет номер телефона пользователя.
    Порядок поиска:
        1. user.phone
        2. связанные объекты profile / patient / person
        3. последняя запись Appointment
    Возвращает:
        Номер телефона или пустую строку,
        если пользователь не аутентифицирован или телефон не найден.
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
        .order_by("-id")
        .first()
    )
    if last:
        return (last.phone or "").strip()

    return


def lk_user_data(request) -> dict[str, Any]:
    """
    Добавляет данные пользователя в контекст шаблонов личного кабинета.
    В контекст передаются:
        lk_full_name — ФИО пользователя
        lk_phone — телефон пользователя
    """
    user = getattr(request, "user", None)
    return {"lk_full_name": _user_full_name(user), "lk_phone": _user_phone(user)}
