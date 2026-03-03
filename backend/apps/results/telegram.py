"""
Telegram-клиент для уведомлений о результатах исследований.
Используется сигналами приложения results
для отправки сообщений пациентам при загрузке новых файлов.
"""

from __future__ import annotations

import requests
from django.conf import settings


def send_telegram_message(chat_id: str, text: str) -> None:
    """
    Отправляет текстовое сообщение в указанный Telegram-чат.
    Параметры:
        chat_id: Идентификатор чата (пользователь или группа).
        text: Текст сообщения.
    Поведение:
        - если TELEGRAM_BOT_TOKEN не настроен — функция ничего не делает;
        - если chat_id пустой — функция ничего не делает;
        - сетевые ошибки не пробрасываются наружу.
    Назначение:
        Используется для простых уведомлений пациента
        о загрузке нового результата исследования.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=8)
