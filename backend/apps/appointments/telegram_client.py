"""
Telegram client for sending messages to Mediscan chat.

Uses Telegram Bot API via HTTPS.
"""

import requests
from django.conf import settings


def send_telegram_message(text: str) -> None:
    """
    Send a Telegram message using Bot API.

    Args:
        text: Message text (Markdown is enabled).

    Notes:
        - If TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured, does nothing.
        - Network errors are swallowed to avoid breaking user flow / tasks.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        # Deliberately silent: telegram is best-effort notification channel
        return