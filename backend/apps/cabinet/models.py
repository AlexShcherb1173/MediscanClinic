"""
Модели приложения личного кабинета (cabinet).
Содержит:
- UserProfile — расширенный профиль пользователя
  с дополнительными данными, используемыми в личном кабинете.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Расширенный профиль пользователя для личного кабинета.
    Модель хранит дополнительные данные, которые не входят
    в стандартную модель пользователя (AUTH_USER_MODEL).
    Поля:
        user: Связь один-к-одному с пользователем.
        telegram_chat_id: Необязательный Telegram chat_id
                          для отправки персональных уведомлений.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    telegram_chat_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self) -> str:
        """
        Возвращает человекочитаемое представление профиля
        для отображения в админке и логах.
        """
        return f"Profile: {self.user}"
