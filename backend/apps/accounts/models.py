"""
Модели приложения accounts.
Содержит кастомную модель пользователя, которая аутентифицируется по телефону вместо username.
Реализовано:
- нормализация телефона при создании пользователя
- нормализация/валидация на уровне модели (clean/save)
- кастомный UserManager для create_user/create_superuser
"""

from __future__ import annotations

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .utils import normalize_phone

# Хранение ТОЛЬКО E.164. Пример: +79991234567
e164_phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{1,14}$",
    message="Введите телефон в формате E.164: +79991234567",
)


class UserManager(BaseUserManager):
    """
    Менеджер пользователей, где уникальным идентификатором является телефон.
    """

    use_in_migrations = True

    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        """
        Создаёт и сохраняет пользователя с нормализованным телефоном.
        Args:
            phone: телефон (любой вводимый формат, будет нормализован до E.164)
            password: пароль (может быть None)
            extra_fields: дополнительные поля модели
        Returns:
            Созданный пользователь.
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
        Создаёт и сохраняет суперпользователя.
        Поддерживает «защиту от ошибки»: если в extra_fields пришёл username,
        используем его как phone (чтобы не ломался createsuperuser).
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
    Кастомная модель пользователя с аутентификацией по телефону.
    Особенности:
        - поле username отключено (не используется)
        - USERNAME_FIELD = phone
        - телефон хранится только в формате E.164 (+7999...)
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
        Нормализует телефон при любом сценарии валидации (admin/forms/serializer).
        """
        super().clean()
        if self.phone:
            self.phone = normalize_phone(self.phone)

    def save(self, *args, **kwargs):
        """
        Нормализует телефон при сохранении (на случай, если full_clean() не вызывали).
        """
        if self.phone:
            # normalize even if someone saved without calling manager or form validation
            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def touch(self) -> None:
        """
        Обновляет отметку последней активности пользователя.
        """
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at"])

    def __str__(self) -> str:
        """
        Возвращает ФИО, если оно заполнено, иначе — телефон.
        """
        return self.full_name or self.phone
