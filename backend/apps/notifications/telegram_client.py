"""
Telegram client for low-level notifications.

This module provides a safe wrapper around Telegram Bot API sendMessage:
- reads token/chat_id from Django settings
- never raises exceptions to the caller (returns bool instead)
- logs failures without leaking secrets

Settings used:
    TELEGRAM_BOT_TOKEN: bot token
    TELEGRAM_CHAT_ID: destination chat id (user or group)
    TELEGRAM_API_BASE: optional API base (default: https://api.telegram.org)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("notifications.telegram")


@dataclass(frozen=True)
class TelegramConfig:
    """
    Runtime Telegram configuration used by the sender.

    Attributes:
        token: bot token
        chat_id: target chat id (string, can be negative for groups)
        api_base: telegram API base url
    """

    token: str
    chat_id: str
    api_base: str = "https://api.telegram.org"


def _get_cfg() -> Optional[TelegramConfig]:
    """
    Build TelegramConfig from Django settings.

    Returns:
        TelegramConfig if both token and chat_id are provided; otherwise None.
    """
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = (getattr(settings, "TELEGRAM_CHAT_ID", "") or "").strip()
    api_base = (
        getattr(settings, "TELEGRAM_API_BASE", "") or ""
    ).strip() or "https://api.telegram.org"

    if not token or not chat_id:
        return None

    return TelegramConfig(token=token, chat_id=str(chat_id), api_base=api_base)


def send_telegram_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Send message to Telegram Bot API.

    This function is intentionally resilient:
    - returns False when Telegram is not configured or request failed
    - does not raise exceptions (so Celery tasks or views won't crash)

    Args:
        text: message text
        parse_mode: Telegram parse mode ("Markdown", "HTML", etc.)

    Returns:
        True if HTTP request returned 2xx, otherwise False.
    """
    cfg = _get_cfg()
    if not cfg:
        logger.warning(
            "Telegram is not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)."
        )
        return False

    # Telegram Bot API message length limit is ~4096 chars for text.
    safe_text = text or ""
    if len(safe_text) > 4096:
        safe_text = safe_text[:4090] + "…"

    url = f"{cfg.api_base}/bot{cfg.token}/sendMessage"
    payload = {
        "chat_id": cfg.chat_id,
        "text": safe_text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        ok = bool(r.ok)
        if not ok:
            # Never log token. Only status + small body excerpt.
            logger.warning(
                "Telegram send failed: status=%s body=%s",
                r.status_code,
                (r.text or "")[:500],
            )
        return ok
    except Exception as exc:
        logger.exception("Telegram send exception: %s", exc)
        return False
