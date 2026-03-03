"""
Модели приложения пациентов (patients).
Приложение хранит данные профиля пациента,
которые не должны находиться в модели аутентификации (AUTH_USER_MODEL).
Если дополнительные поля профиля пациента не требуются,
приложение можно удалить из INSTALLED_APPS.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class PatientProfile(models.Model):
    """
    Дополнительный профиль пациента, связанный с пользователем (1-к-1).
    В этой модели следует хранить только действительно
    пациент-ориентированные данные (медицинские/профильные),
    а не данные аутентификации.
    Поля:
        user: Связь один-к-одному с AUTH_USER_MODEL.
        birth_date: Дата рождения (опционально).
        notes: Внутренние служебные заметки
               (по умолчанию не предназначены для отображения пациенту).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        verbose_name="Пользователь",
    )
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    notes = models.TextField("Заметки", blank=True)

    class Meta:
        verbose_name = "Профиль пациента"
        verbose_name_plural = "Профили пациентов"

    def __str__(self) -> str:
        """
        Возвращает человекочитаемое представление профиля
        для админки и логов.
        """
        return f"PatientProfile: {self.user}"
