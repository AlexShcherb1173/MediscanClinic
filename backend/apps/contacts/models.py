"""
Models for contacts application.

Stores admin-created messages that can be sent to Telegram from Django admin.
"""

from __future__ import annotations

from django.db import models


class AdminTelegramMessage(models.Model):
    """
    Message to be delivered to Telegram from Django admin.

    Fields:
        text: message text (HTML is allowed by telegram sender)
        created_at: creation timestamp
        sent_at: timestamp when message was sent successfully
        is_sent: delivery flag
    """

    text = models.TextField("Текст сообщения")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено", null=True, blank=True)
    is_sent = models.BooleanField("Отправлено", default=False)

    class Meta:
        verbose_name = "Сообщение в Telegram"
        verbose_name_plural = "Сообщения в Telegram"

    def __str__(self) -> str:
        """Short admin representation."""
        return f"Telegram message #{self.pk}"