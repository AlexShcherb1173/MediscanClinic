"""
Custom user model for accounts application.

Implements authentication by phone number instead of username.
Includes:
- phone normalization on user creation
- model-level normalization/validation (clean/save)
- custom UserManager for create_user/create_superuser
"""

from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .utils import normalize_phone

# Enterprise: store ONLY E.164. Example: +79991234567
e164_phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{1,14}$",
    message="Введите телефон в формате E.164: +79991234567",
)


class UserManager(BaseUserManager):
    """
    Custom user manager that uses phone as unique identifier.
    """

    use_in_migrations = True

    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        """
        Create and save a user with normalized phone.
        """
        if not phone:
            raise ValueError("Телефон обязателен")

        phone_norm = normalize_phone(phone)
        extra_fields["phone"] = phone_norm

        user = self.model(**extra_fields)
        user.set_password(password)

        # validate model fields/unique constraints
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_superuser(
        self, phone: str | None = None, password: str | None = None, **extra_fields
    ):
        """
        Create and save a superuser.

        Supports fallback from username -> phone to avoid mistakes in createsuperuser.
        """
        if phone is None and "username" in extra_fields:
            phone = extra_fields.pop("username")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone=phone, password=password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with phone-based authentication.

    Notes:
        - username field is removed (not used)
        - phone is used as USERNAME_FIELD
        - phone stored ONLY in E.164 (+7999...)
    """

    username = None  # remove AbstractUser.username

    phone = models.CharField(
        "Телефон",
        max_length=16,  # '+' + up to 15 digits
        unique=True,
        # null=True,  # временно (нужно для дедупликации)
        # blank=True,  # временно
        validators=[e164_phone_validator],
        db_index=True,
        help_text="Формат хранения: E.164 (например +79991234567).",
    )
    full_name = models.CharField("ФИО", max_length=150, blank=True)
    email = models.EmailField("Email", blank=True)

    last_seen_at = models.DateTimeField("Последняя активность", null=True, blank=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = ["full_name"]

    objects = UserManager()

    def clean(self) -> None:
        """
        Ensure phone is normalized on any validation path (admin/forms/serializers).
        """
        super().clean()
        if self.phone:
            self.phone = normalize_phone(self.phone)

    def save(self, *args, **kwargs):
        """
        Ensure phone is normalized on any save path (even if full_clean not called).
        """
        if self.phone:
            # normalize even if someone saved without calling manager or form validation
            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])

    def __str__(self) -> str:
        """Return full name if available, otherwise phone."""
        return self.full_name or self.phone
