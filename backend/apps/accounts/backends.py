from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .utils import normalize_phone

User = get_user_model()

class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, phone=None, **kwargs):
        if password is None:
            return None

        # поддержим оба варианта: authenticate(username=...) и authenticate(phone=...)
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