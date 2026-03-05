"""
Telegram-клиент для низкоуровневых уведомлений.
Модуль предоставляет безопасную обёртку над Telegram Bot API (sendMessage):
- читает token и chat_id из настроек Django;
- не выбрасывает исключения наружу (возвращает bool);
- логирует ошибки без раскрытия чувствительных данных (token).
Используемые настройки:
    TELEGRAM_BOT_TOKEN — токен бота;
    TELEGRAM_CHAT_ID — идентификатор получателя (пользователь или группа);
    TELEGRAM_API_BASE — базовый URL API (по умолчанию https://api.telegram.org).
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
    Конфигурация Telegram, используемая отправителем сообщений.
    Поля:
        token: Токен Telegram-бота.
        chat_id: Идентификатор целевого чата (строка, может быть отрицательным для групп).
        api_base: Базовый URL Telegram API.
    """

    token: str
    chat_id: str
    api_base: str = "https://api.telegram.org"


def _get_cfg() -> Optional[TelegramConfig]:
    """
    Формирует объект TelegramConfig на основе настроек Django.
    Логика:
        - получает TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID из settings;
        - если одно из значений отсутствует — возвращает None;
        - TELEGRAM_API_BASE используется при наличии,
          иначе применяется значение по умолчанию.
    Возвращает:
        TelegramConfig — при корректной конфигурации;
        None — если Telegram не настроен.
    """
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = (getattr(settings, "TELEGRAM_CHAT_ID", "") or "").strip()
    api_base = (getattr(settings, "TELEGRAM_API_BASE", "") or "").strip() or "https://api.telegram.org"

    if not token or not chat_id:
        return None

    return TelegramConfig(token=token, chat_id=str(chat_id), api_base=api_base)


def send_telegram_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Отправляет сообщение в Telegram через Bot API.
    Функция реализована в режиме best-effort:
        - при отсутствии конфигурации возвращает False;
        - при сетевых ошибках не выбрасывает исключения;
        - логирует сбои без раскрытия токена.
    Параметры:
        text (str): Текст сообщения.
        parse_mode (str): Режим форматирования Telegram
                          ("Markdown", "HTML" и др.).
    Особенности:
        - текст автоматически обрезается до ~4096 символов
          (ограничение Telegram API);
        - предпросмотр ссылок отключён.
    Возвращает:
        bool: True при успешном HTTP-ответе (2xx),
              False при ошибке или отсутствии конфигурации.
    """
    cfg = _get_cfg()
    if not cfg:
        logger.warning("Telegram is not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID).")
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
