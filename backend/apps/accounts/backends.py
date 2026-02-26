"""
Authentication backend for phone-based login.

PhoneBackend supports both:
- authenticate(username="<phone>", password=...)
- authenticate(phone="<phone>", password=...)

Phone is normalized using accounts.utils.normalize_phone().
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .utils import normalize_phone

User = get_user_model()


class PhoneBackend(ModelBackend):
    """
    Authenticate users by phone number.

    The backend expects a password and either username or phone.
    """

    def authenticate(self, request, username=None, password=None, phone=None, **kwargs):
        """
        Authenticate user by phone.

        Args:
            request: HttpRequest (unused, but required by Django signature)
            username: phone value when called via authenticate(username=...)
            password: raw password
            phone: phone value when called via authenticate(phone=...)
            kwargs: ignored

        Returns:
            User instance if credentials are valid, otherwise None.
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