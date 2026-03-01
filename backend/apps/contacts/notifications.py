"""
Notification helpers for contacts application.

Provides:
- notify_contact_email: send email to admin
- notify_contact_telegram: send Telegram message to admin chat via Bot API

Email errors are raised (fail_silently=False) because this is a contact channel.
Telegram errors are silently ignored if credentials are missing.
"""

from __future__ import annotations

import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import EmailMessage


def _as_email(value) -> str:
    """
    Normalize email-like setting to string.

    Accepts strings and single-element tuples/lists.
    """
    if isinstance(value, (tuple, list)):
        value = value[0] if value else ""
    return str(value).strip()


def notify_contact_email(subject: str, text: str) -> None:
    """
    Send contact email to admin mailbox.

    Uses settings:
        DEFAULT_FROM_EMAIL
        CONTACTS_ADMIN_EMAIL (fallbacks to DEFAULT_FROM_EMAIL)
    """
    from_email = _as_email(getattr(settings, "DEFAULT_FROM_EMAIL", ""))
    to_email = _as_email(getattr(settings, "CONTACTS_ADMIN_EMAIL", "")) or from_email

    if not from_email:
        raise ValueError("DEFAULT_FROM_EMAIL is empty/invalid")
    if not to_email:
        raise ValueError("CONTACTS_ADMIN_EMAIL is empty/invalid")

    msg = EmailMessage(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[to_email],
        reply_to=[from_email],
    )
    msg.send(fail_silently=False)


def notify_contact_telegram(text: str) -> None:
    """
    Send Telegram message to admin chat.

    Uses:
        TELEGRAM_BOT_TOKEN
        TELEGRAM_ADMIN_CHAT_ID

    If token/chat_id is missing, does nothing.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_ADMIN_CHAT_ID", None)

    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=10) as resp:
        _ = resp.read()  # response body not used
