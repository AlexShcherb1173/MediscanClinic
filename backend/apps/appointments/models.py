from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.services.models import Service
from apps.staff.models import Doctor
from apps.promos.models import Promo


phone_validator = RegexValidator(
    regex=r"^\+?\d[\d\s\-\(\)]{8,20}$",
    message="Введите телефон в формате +79990000000 (можно пробелы/скобки/дефисы).",
)


class AppointmentSlot(models.Model):
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
            models.UniqueConstraint(
                fields=["service", "starts_at"],
                name="uniq_service_starts_at",
            )
        ]

    def __str__(self) -> str:
        return f"{self.service} — {self.starts_at:%d.%m %H:%M}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CONFIRMED = "confirmed", "Подтверждена"
        COMPLETED = "completed", "Завершена"
        CANCELED = "canceled", "Отменена"

    # ✅ Услуга — опционально (но чаще будет заполнена)
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Услуга",
        null=True,
        blank=True,
    )

    # ✅ Слот (основной источник времени записи)
    slot = models.ForeignKey(
        "appointments.AppointmentSlot",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Слот",
        null=True,
        blank=True,
    )

    # ✅ preferred_datetime оставляем для удобства индексов/ограничений/фильтров
    preferred_datetime = models.DateTimeField("Дата и время", null=True, blank=True)

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

    full_name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=24, validators=[phone_validator])
    email = models.EmailField("Email", blank=True, validators=[EmailValidator()])

    comment = models.TextField("Комментарий", blank=True)

    reminded_at = models.DateTimeField("Напоминание отправлено", null=True, blank=True)
    reminder_email_sent = models.BooleanField("Email-напоминание отправлено", default=False)
    reminder_telegram_sent = models.BooleanField("Telegram-напоминание отправлено", default=False)

    status = models.CharField(
        "Статус",
        max_length=12,
        choices=Status.choices,
        default=Status.NEW,
    )

    created_at = models.DateTimeField("Создана", auto_now_add=True)

    reminder_24h_sent = models.BooleanField("Напоминание 24ч отправлено", default=False)
    reminder_2h_sent = models.BooleanField("Напоминание 2ч отправлено", default=False)

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
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "preferred_datetime"],
                condition=Q(doctor__isnull=False) & Q(preferred_datetime__isnull=False),
                name="uniq_doctor_datetime",
            ),
            models.UniqueConstraint(
                fields=["service", "preferred_datetime"],
                condition=Q(service__isnull=False) & Q(preferred_datetime__isnull=False),
                name="uniq_service_datetime",
            ),
        ]

    def clean(self):
        super().clean()

        # slot обязателен для новой UX-логики
        if not self.slot:
            raise ValidationError("Выберите время записи (слот).")

        # должна быть выбрана услуга или врач
        if not self.service and not self.doctor:
            raise ValidationError("Необходимо выбрать услугу или врача для записи.")

    def save(self, *args, **kwargs):
        # ✅ всегда синхронизируем preferred_datetime со слотом
        if self.slot and self.slot.starts_at:
            self.preferred_datetime = self.slot.starts_at
            # также удобно подтянуть service из слота, если не заполнена
            if not self.service_id and getattr(self.slot, "service_id", None):
                self.service_id = self.slot.service_id

        super().save(*args, **kwargs)

    def __str__(self) -> str:
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