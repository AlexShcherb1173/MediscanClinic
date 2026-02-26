"""
Telegram client used by Django admin actions.

Unlike notify_contact_telegram(), this client is strict:
- raises RuntimeError when token/chat_id is missing
- raises on HTTP errors
"""

from __future__ import annotations

import requests
from django.conf import settings


def send_telegram_message(text: str, chat_id: str | None = None) -> None:
    """
    Send Telegram message using Bot API (JSON payload).

    Args:
        text: message text (HTML supported via parse_mode)
        chat_id: override chat id; defaults to TELEGRAM_ADMIN_CHAT_ID

    Raises:
        RuntimeError: if bot token or chat id are missing
        requests.HTTPError: for non-2xx responses
    """
    if not getattr(settings, "TELEGRAM_BOT_TOKEN", ""):
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

    chat_id = chat_id or getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", "")
    if not chat_id:
        raise RuntimeError("TELEGRAM_ADMIN_CHAT_ID is empty")

    api_url = getattr(settings, "TELEGRAM_API_URL", "")
    if not api_url:
        api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    url = f"{api_url}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()