from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

from apps.services.models import Service


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

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Услуга",
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
        ]
        constraints = [
            # запрет двойной записи на одну услугу в то же время
            models.UniqueConstraint(
                fields=["service", "preferred_datetime"],
                name="uniq_service_datetime",
            )
        ]

    def __str__(self) -> str:
        return f"{self.full_name} → {self.service} ({self.preferred_datetime:%Y-%m-%d %H:%M})"