"""
Telegram-клиент для использования в Django Admin.
В отличие от notify_contact_telegram(), данный клиент работает в строгом режиме:
- выбрасывает RuntimeError при отсутствии обязательных настроек;
- выбрасывает исключение при HTTP-ошибках Telegram API.
Используется в административных действиях, где ошибки должны быть явно видимы.
"""

from __future__ import annotations

import requests
from django.conf import settings


def send_telegram_message(text: str, chat_id: str | None = None) -> None:
    """
    Отправляет сообщение в Telegram через Bot API (JSON-пayload).
    Параметры:
        text (str): Текст сообщения (поддерживается форматирование HTML).
        chat_id (str | None): Идентификатор чата. Если не указан,
                              используется TELEGRAM_ADMIN_CHAT_ID из настроек.
    Используемые настройки:
        - TELEGRAM_BOT_TOKEN (обязателен);
        - TELEGRAM_ADMIN_CHAT_ID (обязателен, если chat_id не передан);
        - TELEGRAM_API_URL (опционально, по умолчанию используется api.telegram.org).
    Поведение:
        - формирует POST-запрос к <api_url>/sendMessage;
        - отправляет JSON-пayload с parse_mode="HTML";
        - отключает предпросмотр ссылок.
    Исключения:
        RuntimeError:
            - если TELEGRAM_BOT_TOKEN не задан;
            - если chat_id отсутствует.
        requests.HTTPError:
            - при получении неуспешного HTTP-ответа (raise_for_status()).
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
