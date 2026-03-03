"""
Вспомогательные функции уведомлений для приложения контактов (contacts).
Предоставляет:
- notify_contact_email — отправка email администратору;
- notify_contact_telegram — отправка сообщения в Telegram-чат администратора через Bot API.
Особенности:
- Ошибки отправки email не подавляются (fail_silently=False),
  так как это основной канал связи с пользователем.
- Telegram используется как дополнительный канал и может быть отключён,
  если отсутствуют необходимые настройки.
"""

from __future__ import annotations

import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import EmailMessage


def _as_email(value) -> str:
    """
    Приводит значение настройки к строке email.
    Поддерживает:
        - строку;
        - кортеж или список с одним элементом.
    Параметры:
        value: Значение из settings (str | list | tuple).
    Возвращает:
        str: Очищенная строка email (или пустая строка).
    """
    if isinstance(value, (tuple, list)):
        value = value[0] if value else ""
    return str(value).strip()


def notify_contact_email(subject: str, text: str) -> None:
    """
    Отправляет email администратору из формы контактов.
    Использует настройки:
        - DEFAULT_FROM_EMAIL — адрес отправителя;
        - CONTACTS_ADMIN_EMAIL — адрес получателя
          (если не задан, используется DEFAULT_FROM_EMAIL).
    Поведение:
        - при отсутствии корректных настроек выбрасывает ValueError;
        - отправляет письмо через EmailMessage;
        - fail_silently=False — ошибки SMTP не подавляются.
    Параметры:
        subject (str): Тема письма.
        text (str): Текст письма (plain text).
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
    Отправляет сообщение в Telegram-чат администратора.
    Использует настройки:
        - TELEGRAM_BOT_TOKEN;
        - TELEGRAM_ADMIN_CHAT_ID.
    Поведение:
        - если токен или chat_id отсутствуют — функция завершает выполнение;
        - отправка выполняется через Telegram Bot API (sendMessage);
        - используется parse_mode="HTML";
        - предпросмотр ссылок отключён.
    Параметры:
        text (str): Текст сообщения.
    Исключения:
        Ошибки сети не перехватываются — в случае сбоя будет выброшено исключение.
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
