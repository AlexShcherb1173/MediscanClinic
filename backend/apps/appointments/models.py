"""
Модели приложения записей на приём.
Содержит:
- AppointmentSlot — временные слоты, доступные для записи по конкретной услуге.
- Appointment — запись пациента на приём с контактными данными и привязками
  к услуге/слоту/врачу/акции/пользователю.
Включает правила валидации и ограничения на уровне БД, предотвращающие
двойную запись на один и тот же слот.
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

phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{1,14}$",
    message="Введите телефон в формате E.164: +79991234567",
)
"""
Валидатор телефона для модели записи.
Формат E.164:
- начинается с символа '+';
- первая цифра (код страны) — 1..9;
- далее только цифры;
- общая длина номера (без '+') — до 15 цифр.
"""


class AppointmentSlot(models.Model):
    """
    Временной слот для записи на конкретную услугу.
    Слот описывает интервал времени (starts_at → ends_at), который можно забронировать
    для выбранной услуги.
    Поля:
        service: Услуга, для которой доступен данный слот.
        starts_at: Дата и время начала слота.
        ends_at: Дата и время окончания слота.
        is_active: Признак доступности слота (можно отключать без удаления).
        is_booked: Признак занятости слота (быстрый флаг для UI/логики).
    Ограничения:
        - Уникальность (service, starts_at) не позволяет создать два одинаковых слота
          для одной услуги на одно и то же время.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="slots")
    starts_at = models.DateTimeField("Начало слота")
    ends_at = models.DateTimeField("Конец слота")
    is_active = models.BooleanField("Активен", default=True)
    is_booked = models.BooleanField("Занят", default=False)

    class Meta:
        """
        Параметры модели AppointmentSlot.

        - ordering: сортировка слотов по времени начала.
        - indexes: индексы для ускорения фильтраций (по услуге/времени и по статусам).
        - constraints: уникальный слот по (service, starts_at).
        """

        ordering = ("starts_at",)
        indexes = [
            models.Index(fields=["service", "starts_at"]),
            models.Index(fields=["is_active", "is_booked"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["service", "starts_at"], name="uniq_slot_service_starts_at"),
        ]

    def __str__(self) -> str:
        """
        Возвращает человекочитаемое представление слота.
        Используется в админке и логах.
        """
        return f"{self.service} — {self.starts_at:%d.%m %H:%M}"


class Appointment(models.Model):
    """
    Запись пациента на приём.
    Модель хранит данные пациента и информацию о записи, включая:
    - услугу и выбранный слот,
    - врача (опционально),
    - акцию (опционально),
    - пользователя (если запись создана из личного кабинета/авторизованного профиля).
    Также хранит флаги и дату отправки напоминаний (email/telegram, 24ч/2ч).
    """

    class Status(models.TextChoices):
        """
        Статусы записи.
        NEW — новая (создана, ожидает обработки).
        CONFIRMED — подтверждена клиникой/администратором.
        COMPLETED — визит состоялся.
        CANCELED — отменена.
        """

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
        Валидация на уровне модели (вызывается в full_clean()).
        Правила:
        - телефон приводится к формату E.164 (нормализация применяется для всех точек входа:
          admin/ORM/forms);
        - слот обязателен (без слота запись не считается корректной).
        Вызывает:
            ValidationError: если слот не выбран.
        """
        super().clean()

        if self.phone:
            self.phone = normalize_phone(self.phone)

        if not self.slot:
            raise ValidationError("Выберите слот для записи.")

    def save(self, *args, **kwargs):
        """
        Сохраняет запись, гарантируя нормализацию телефона.
        Нормализация выполняется даже если full_clean() не был вызван
        (например, при сохранении из кода напрямую через ORM).
        """
        if self.phone:
            self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Возвращает человекочитаемое представление записи.
        Формат строится из доступных частей: имя пациента → врач/услуга/акция → дата/время.
        Используется в админке и логах.
        """
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
