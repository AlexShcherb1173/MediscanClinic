from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

from apps.services.models import Service
from apps.staff.models import Doctor


phone_validator = RegexValidator(
    regex=r"^\+?\d[\d\s\-\(\)]{8,20}$",
    message="Введите телефон в формате +79990000000 (можно пробелы/скобки/дефисы).",
)


class Appointment(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        CONFIRMED = "confirmed", "Подтверждена"
        COMPLETED = "completed", "Завершена"
        CANCELED = "canceled", "Отменена"

    # ✅ Услуга — теперь НЕ обязательна
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Услуга",
        null=True,
        blank=True,
    )

    # ✅ Врач — опционально
    doctor = models.ForeignKey(
        Doctor,
        related_name="appointments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Врач",
    )

    full_name = models.CharField("Имя", max_length=120)
    phone = models.CharField("Телефон", max_length=24, validators=[phone_validator])

    preferred_datetime = models.DateTimeField("Желаемые дата/время")
    comment = models.TextField("Комментарий", blank=True)

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
        ]
        constraints = [
            # ❌ нельзя две записи к одному врачу в одно время
            models.UniqueConstraint(
                fields=["doctor", "preferred_datetime"],
                condition=Q(doctor__isnull=False),
                name="uniq_doctor_datetime",
            ),
            # ❌ нельзя две записи на одну услугу в одно время
            models.UniqueConstraint(
                fields=["service", "preferred_datetime"],
                condition=Q(service__isnull=False),
                name="uniq_service_datetime",
            ),
        ]

    def clean(self):
        """
        Бизнес-валидация:
        - должна быть выбрана услуга или врач
        """
        super().clean()
        if not self.service and not self.doctor:
            raise ValidationError(
                "Необходимо выбрать услугу или врача для записи."
            )

    def __str__(self) -> str:
        parts = [self.full_name]

        if self.doctor:
            parts.append(f"к врачу {self.doctor.full_name}")

        if self.service:
            parts.append(f"на услугу «{self.service.name}»")

        parts.append(self.preferred_datetime.strftime("%Y-%m-%d %H:%M"))
        return " → ".join(parts)