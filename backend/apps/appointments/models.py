"""
Models for appointments application.

Contains:
- AppointmentSlot: time slots available for booking per service
- Appointment: booking record with patient data, optional doctor/promo/user

Includes validation rules and DB constraints to prevent double-booking.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.accounts.utils import normalize_phone
from apps.promos.models import Promo
from apps.services.models import Service
from apps.staff.models import Doctor

# Enterprise: store only E.164 (+79991234567)
phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{1,14}$",
    message="Введите телефон в формате E.164: +79991234567",
)
"""
Phone validator for appointment model.

E.164 rules:
- starts with '+'
- country code 1..3 digits (first digit 1..9)
- total digits up to 15
"""


class AppointmentSlot(models.Model):
    """
    Booking slot for a specific service.

    Attributes:
        service: Service which can be booked in this slot.
        starts_at: Start datetime of the slot.
        ends_at: End datetime of the slot.
        is_active: Controls slot availability.
        is_booked: Flag used to mark slot as occupied.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="slots")
    starts_at = models.DateTimeField("Начало слота")
    ends_at = models.DateTimeField("Конец слота")
    is_active = models.BooleanField("Активен", default=True)
    is_booked = models.BooleanField("Занят", default=False)

    class Meta:
        ordering = ("starts_at",)
        indexes = [
            models.Index(fields=["service", "starts_at"]),
            models.Index(fields=["is_active", "is_booked"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["service", "starts_at"], name="uniq_slot_service_starts_at"),
        ]

    def __str__(self) -> str:
        """Human-readable slot representation."""
        return f"{self.service} — {self.starts_at:%d.%m %H:%M}"


class Appointment(models.Model):
    """
    Appointment (booking) model.

    Can be linked to:
    - service
    - time slot (required by `clean()` rule)
    - doctor
    - promo
    - authenticated user

    Also stores patient contact details and reminder flags.
    """

    class Status(models.TextChoices):
        """Allowed appointment statuses."""
        NEW = "new", "Новая"
        CONFIRMED = "confirmed", "Подтверждена"
        COMPLETED = "completed", "Завершена"
        CANCELED = "canceled", "Отменена"

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Услуга",
        null=True,
        blank=True,
    )

    slot = models.ForeignKey(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Слот",
        null=True,
        blank=True,
    )

    doctor = models.ForeignKey(
        Doctor,
        related_name="appointments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Врач",
    )

    promo = models.ForeignKey(
        Promo,
        related_name="appointments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Акция",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        verbose_name="Пользователь",
    )

    full_name = models.CharField("Имя", max_length=120)

    # Enterprise: store normalized E.164
    phone = models.CharField(
        "Телефон",
        max_length=16,  # '+' + max 15 digits
        validators=[phone_validator],
    )

    email = models.EmailField("Email", blank=True, validators=[EmailValidator()])
    comment = models.TextField("Комментарий", blank=True)

    preferred_datetime = models.DateTimeField("Дата/время записи", null=True, blank=True)

    reminded_at = models.DateTimeField("Напоминание отправлено", null=True, blank=True)
    reminder_email_sent = models.BooleanField("Email-напоминание отправлено", default=False)
    reminder_telegram_sent = models.BooleanField("Telegram-напоминание отправлено", default=False)
    reminder_24h_sent = models.BooleanField("Напоминание 24ч отправлено", default=False)
    reminder_2h_sent = models.BooleanField("Напоминание 2ч отправлено", default=False)

    status = models.CharField(
        "Статус",
        max_length=12,
        choices=Status.choices,
        default=Status.NEW,
    )

    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["preferred_datetime"]),
            models.Index(fields=["doctor"]),
            models.Index(fields=["service"]),
            models.Index(fields=["promo"]),
            models.Index(fields=["slot"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(slot__isnull=False),
                name="uniq_appointment_slot",
            ),
        ]

    def clean(self):
        """
        Model-level validation.

        Rules:
            - a slot must be selected
            - phone must be normalized to E.164
        """
        super().clean()

        # normalize phone for all entry points (admin/ORM/forms)
        if self.phone:
            self.phone = normalize_phone(self.phone)

        if not self.slot:
            raise ValidationError("Выберите слот для записи.")

    def save(self, *args, **kwargs):
        """
        Ensure phone is normalized even if full_clean() not called.
        """
        if self.phone:
            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Readable representation for admin and logs."""
        parts = [self.full_name]
        if self.doctor:
            parts.append(f"к врачу {self.doctor.full_name}")
        if self.service:
            parts.append(f"на услугу «{self.service.name}»")
        if self.promo:
            parts.append(f"(акция: {self.promo.title})")
        if self.preferred_datetime:
            parts.append(self.preferred_datetime.strftime("%Y-%m-%d %H:%M"))
        return " → ".join(parts)