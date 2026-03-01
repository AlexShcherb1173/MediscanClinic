"""
Telegram client for results notifications.

Used by signals to notify patients about newly uploaded results.
"""

from __future__ import annotations

import requests
from django.conf import settings


def send_telegram_message(chat_id: str, text: str) -> None:
    """
    Send text message to a specific Telegram chat.

    If TELEGRAM_BOT_TOKEN or chat_id is missing, silently does nothing.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=8)
