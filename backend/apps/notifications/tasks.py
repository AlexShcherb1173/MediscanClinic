"""
Celery-задачи приложения уведомлений (notifications).
В текущей версии содержит:
- send_telegram_text_task — отправку текстовых сообщений в Telegram
  через telegram_client.
Задача настроена на автоматические повторные попытки (autoretry)
с экспоненциальной задержкой и jitter.
"""

from __future__ import annotations

import logging

from celery import shared_task

from .telegram_client import send_telegram_message

logger = logging.getLogger("notifications")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_telegram_text_task(self, text: str) -> None:
    """
    Отправляет текстовое сообщение в Telegram.
    Параметры:
        text (str): Текст сообщения.
    Поведение:
        - вызывает send_telegram_message();
        - если отправка неуспешна (ok=False),
          выбрасывает RuntimeError для запуска механизма autoretry.
    Повторы:
        - до 5 попыток;
        - экспоненциальный backoff;
        - с добавлением jitter для уменьшения эффекта «шторма» запросов.
    """
    ok = send_telegram_message(text)
    if not ok:
        raise RuntimeError("Telegram send failed")
