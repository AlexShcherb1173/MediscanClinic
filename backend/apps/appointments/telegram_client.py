"""
Клиент Telegram для отправки сообщений в чат Mediscan.
Использует Telegram Bot API по HTTPS.
Предназначен для серверной отправки служебных уведомлений.
"""

import requests
from django.conf import settings


def send_telegram_message(text: str) -> None:
    """
    Отправляет сообщение в Telegram через Bot API.
    Параметры:
        text (str): Текст сообщения. Поддерживается форматирование Markdown.
    Логика работы:
        - Получает TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID из настроек.
        - Формирует запрос к https://api.telegram.org/bot<token>/sendMessage.
        - Отправляет сообщение с отключённым предпросмотром ссылок.
    Поведение при отсутствии настроек:
        - Если TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы,
          функция завершает выполнение без отправки.
    Обработка ошибок:
        - Сетевые и иные исключения перехватываются.
        - Ошибки намеренно не пробрасываются наружу,
          так как Telegram используется как best-effort канал уведомлений
          и не должен прерывать выполнение бизнес-логики или Celery-задач.
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
       return
