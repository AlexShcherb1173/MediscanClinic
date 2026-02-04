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
    ok = send_telegram_message(text)
    if not ok:
        # чтобы сработал autoretry_for — можно явно бросить исключение
        raise RuntimeError("Telegram send failed")