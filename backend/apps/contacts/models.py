from django.db import models

class AdminTelegramMessage(models.Model):
    text = models.TextField("Текст сообщения")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено", null=True, blank=True)
    is_sent = models.BooleanField("Отправлено", default=False)

    class Meta:
        verbose_name = "Сообщение в Telegram"
        verbose_name_plural = "Сообщения в Telegram"

    def __str__(self):
        return f"Telegram message #{self.pk}"