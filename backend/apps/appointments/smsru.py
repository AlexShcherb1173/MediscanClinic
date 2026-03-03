"""
Обёртка для работы с API sms.ru.
Предоставляет функцию `smsru_send`, которая отправляет SMS через API sms.ru
и возвращает результат в виде кортежа:
- (True, sms_id) — при успешной отправке
- (False, error_message) — при ошибке
Функция предназначена для серверного использования,
включает логирование HTTP-ответов и ошибок для отладки.
"""

from __future__ import annotations

import logging

import requests
from django.conf import settings

from .utils import normalize_phone_for_smsru  # поправь импорт под твой реальный модуль/путь

logger = logging.getLogger("appointments.sms")


def smsru_send(to_phone: str, message: str) -> tuple[bool, str]:
    """
    Отправляет SMS-сообщение через API sms.ru.
    Параметры:
        to_phone (str): Номер телефона в произвольном формате
                        (может содержать '+', пробелы, скобки и т.д.).
        message (str): Текст SMS-сообщения.
    Возвращает:
        tuple[bool, str]:
            - (True, sms_id) — сообщение успешно отправлено;
            - (False, error_message) — произошла ошибка.
    Логика работы:
        1. Получает API-ключ из settings.SMS_RU_API_ID.
        2. Нормализует номер телефона через normalize_phone_for_smsru().
        3. Формирует POST-запрос к https://sms.ru/sms/send.
        4. Обрабатывает HTTP-ошибки и ошибки разбора JSON.
        5. Проверяет общий статус ответа (status == "OK").
        6. Проверяет статус отправки для конкретного номера.
        7. Возвращает sms_id при успехе.
    Требования к настройкам:
        - SMS_RU_API_ID — обязателен.
        - SMS_SENDER — опциональное имя отправителя.
    Обработка ошибок:
        - При отсутствии API-ключа возвращает ошибку без запроса к API.
        - При некорректном номере возвращает ошибку.
        - При HTTP/JSON-ошибках возвращает сообщение об ошибке.
        - Все исключения логируются через logger.
    Исключения наружу не пробрасываются (fail-safe поведение).
    """
    api_id = getattr(settings, "SMS_RU_API_ID", "") or ""
    if not api_id:
        logger.warning("sms.ru: SMS_RU_API_ID is empty")
        return False, "SMS_RU_API_ID is empty"

    to_norm = normalize_phone_for_smsru(to_phone)
    if not to_norm:
        logger.warning("sms.ru: empty/invalid phone raw=%r", to_phone)
        return False, "Empty phone"

    url = "https://sms.ru/sms/send"
    data = {"api_id": api_id, "to": to_norm, "msg": message, "json": 1}

    sender = getattr(settings, "SMS_SENDER", "") or ""
    if sender:
        data["from"] = sender

    try:
        r = requests.post(url, data=data, timeout=15)
        logger.info("sms.ru HTTP %s for to=%s", r.status_code, to_norm)
        r.raise_for_status()
        payload = r.json()
        logger.info("sms.ru response for to=%s: %s", to_norm, payload)
    except Exception as e:
        logger.exception("sms.ru request failed for to=%s: %s", to_norm, e)
        return False, f"HTTP/JSON error: {e}"

    if payload.get("status") != "OK":
        logger.error("sms.ru status!=OK: %s", payload)
        return (
            False,
            f"sms.ru error {payload.get('status_code')}: {payload.get('status_text')}",
        )

    sms_info = (payload.get("sms") or {}).get(to_norm) or {}
    if sms_info.get("status") != "OK":
        logger.error("sms.ru per-number error to=%s: %s", to_norm, sms_info)
        return (
            False,
            f"sms to {to_norm} error {sms_info.get('status_code')}: {sms_info.get('status_text')}",
        )

    sms_id = sms_info.get("sms_id", "OK")
    logger.info("sms.ru sent ok to=%s sms_id=%s", to_norm, sms_id)
    return True, sms_id
