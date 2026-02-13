import requests
from django.conf import settings

def send_telegram_message(text: str, chat_id: str | None = None) -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")
    chat_id = chat_id or settings.TELEGRAM_ADMIN_CHAT_ID
    if not chat_id:
        raise RuntimeError("TELEGRAM_ADMIN_CHAT_ID is empty")

    url = f"{settings.TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()