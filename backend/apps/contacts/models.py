"""
Модели приложения контактов (contacts).
Хранит сообщения, создаваемые администратором,
которые могут быть отправлены в Telegram из Django Admin.
"""

from __future__ import annotations

from django.db import models


class AdminTelegramMessage(models.Model):
    """
    Сообщение для отправки в Telegram из административной панели.
    Модель используется администраторами для создания служебных
    уведомлений, которые отправляются в Telegram вручную
    (через action) или автоматически при сохранении.
    Поля:
        text: Текст сообщения (допускается форматирование,
              поддерживаемое Telegram-ботом).
        created_at: Дата и время создания записи.
        sent_at: Дата и время успешной отправки.
        is_sent: Флаг успешной доставки сообщения.
    """

    text = models.TextField("Текст сообщения")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено", null=True, blank=True)
    is_sent = models.BooleanField("Отправлено", default=False)

    class Meta:
        verbose_name = "Сообщение в Telegram"
        verbose_name_plural = "Сообщения в Telegram"

    def __str__(self) -> str:
        """
        Возвращает краткое представление объекта
        для отображения в админке и логах.
        """
        return f"Telegram message #{self.pk}"
