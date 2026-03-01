from __future__ import annotations

import re

import phonenumbers
from django.core.exceptions import ValidationError

E164_RE = re.compile(r"^\+[1-9]\d{1,14}$")


def normalize_phone(raw: str, default_region: str = "RU") -> str:
    """
    Normalize phone to E.164 format: +79991234567

    Accepts user input with spaces/brackets/dashes.
    Validates number using `phonenumbers` and returns E.164 string.
    """
    if raw is None:
        raise ValidationError("Телефон обязателен.")

    value = str(raw).strip()
    if not value:
        raise ValidationError("Телефон обязателен.")

    # keep digits and leading '+'
    value = re.sub(r"[^\d+]", "", value)

    try:
        parsed = phonenumbers.parse(value, None if value.startswith("+") else default_region)
    except phonenumbers.NumberParseException:
        raise ValidationError("Введите корректный номер телефона.")

    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError("Введите корректный номер телефона.")

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    if not E164_RE.match(e164):
        raise ValidationError("Введите корректный номер телефона.")

    return e164