"""
Бэкенд аутентификации по номеру телефона.

PhoneBackend поддерживает оба варианта вызова:
- authenticate(username="<телефон>", password=...)
- authenticate(phone="<телефон>", password=...)

Номер телефона предварительно нормализуется через
accounts.utils.normalize_phone().
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .utils import normalize_phone

User = get_user_model()


class PhoneBackend(ModelBackend):
    """
    Бэкенд аутентификации пользователя по номеру телефона.
    Ожидает пароль и значение телефона,
    переданное либо в параметре username, либо phone.
    """

    def authenticate(self, request, username=None, password=None, phone=None, **kwargs):
        """
        Аутентифицирует пользователя по номеру телефона.
        Аргументы:
            request: HttpRequest (не используется, но обязателен по сигнатуре Django)
            username: номер телефона при вызове authenticate(username=...)
            password: пароль в открытом виде
            phone: номер телефона при вызове authenticate(phone=...)
            kwargs: дополнительные параметры (игнорируются)
        Возвращает:
            Объект User при успешной аутентификации,
            иначе — None.
        """
        if password is None:
            return None

        raw_phone = phone or username
        if not raw_phone:
            return None

        phone_norm = normalize_phone(raw_phone)

        try:
            user = User.objects.get(phone=phone_norm)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
