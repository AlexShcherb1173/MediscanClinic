from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger("notifications.telegram")


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    chat_id: str  # куда слать (твой id/группа)
    api_base: str = "https://api.telegram.org"


def _get_cfg() -> Optional[TelegramConfig]:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or ""

    if not token or not chat_id:
        return None

    return TelegramConfig(token=token, chat_id=str(chat_id))


def send_telegram_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Низкоуровневая отправка сообщения в Telegram.
    Возвращает True/False, исключения наружу не бросаем (чтобы не валить задачи).
    """
    cfg = _get_cfg()
    if not cfg:
        logger.warning("Telegram is not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID).")
        return False

    url = f"{cfg.api_base}/bot{cfg.token}/sendMessage"
    payload = {
        "chat_id": cfg.chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        ok = bool(r.ok)
        if not ok:
            # ❗️ НЕ логируем token. Только статус/текст ошибки
            logger.warning("Telegram send failed: status=%s body=%s", r.status_code, r.text[:500])
        return ok
    except Exception as exc:
        logger.exception("Telegram send exception: %s", exc)
        return False