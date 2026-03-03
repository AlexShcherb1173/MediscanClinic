from __future__ import annotations

from dataclasses import dataclass

from apps.accounts.utils import normalize_phone
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


@dataclass(frozen=True)
class ContactValue:
    """
    Нормализованное контактное значение.
    Атрибуты:
        kind: тип контакта — "phone" или "email"
        value: нормализованное значение:
               - телефон в формате E.164 (+79991234567)
               - email в нижнем регистре
    """

    kind: str  # "phone" | "email"
    value: str  # E.164 phone or lowercased email


_email_validator = EmailValidator()


def normalize_phone_or_email(raw: str) -> ContactValue:
    """
    Нормализует строку как телефон или email.
    Логика:
        - Если строка содержит "@", считается email:
            - проходит валидацию
            - приводится к нижнему регистру
        - Иначе считается телефоном:
            - нормализуется через normalize_phone()
            - приводится к формату E.164
    Аргументы:
        raw: исходная строка, введённая пользователем
    Возвращает:
        ContactValue с типом ("phone" | "email") и нормализованным значением.
    Исключения:
        ValidationError — если значение пустое или некорректное.
    """
    if raw is None:
        raise ValidationError("Укажите телефон или email.")

    value = str(raw).strip()
    if not value:
        raise ValidationError("Укажите телефон или email.")

    # Heuristic: if contains '@' treat as email
    if "@" in value:
        try:
            _email_validator(value)
        except ValidationError:
            raise ValidationError("Введите корректный email.")
        return ContactValue(kind="email", value=value.lower())

    # Otherwise treat as phone
    phone = normalize_phone(value)  # raises ValidationError with good message
    return ContactValue(kind="phone", value=phone)
