"""
Custom user model for accounts application.

Implements authentication by phone number instead of username.
Includes:
- phone normalization on user creation
- custom UserManager for create_user/create_superuser
"""

from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .utils import normalize_phone


phone_validator = RegexValidator(
    regex=r"^\+?\d[\d\s\-\(\)]{8,20}$",
    message="Введите телефон в формате +79990000000 (можно пробелы/скобки/дефисы).",
)


class UserManager(BaseUserManager):
    """
    Custom user manager that uses phone as unique identifier.
    """

    use_in_migrations = True

    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        """
        Create and save a user with normalized phone.

        Args:
            phone: raw phone value (will be normalized)
            password: plain password (optional)
            extra_fields: additional fields for user model

        Returns:
            Created User instance.

        Raises:
            ValueError: if phone is empty.
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

    def create_superuser(self, phone: str | None = None, password: str | None = None, **extra_fields):
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
    """

    username = None  # remove AbstractUser.username

    phone = models.CharField(
        "Телефон",
        max_length=24,
        unique=True,
        validators=[phone_validator],
        db_index=True,
    )
    full_name = models.CharField("ФИО", max_length=150, blank=True)
    email = models.EmailField("Email", blank=True)

    last_seen_at = models.DateTimeField("Последняя активность", null=True, blank=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = ["full_name"]

    objects = UserManager()

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])

    def __str__(self) -> str:
        """Return full name if available, otherwise phone."""
        return self.full_name or self.phone