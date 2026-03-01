from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from apps.accounts.utils import normalize_phone


@dataclass(frozen=True)
class ContactValue:
    """Normalized contact value."""

    kind: str  # "phone" | "email"
    value: str  # E.164 phone or lowercased email


_email_validator = EmailValidator()


def normalize_phone_or_email(raw: str) -> ContactValue:
    """
    Accepts either phone or email in a single field.
    - email -> validates + lower()
    - phone -> normalize_phone() -> E.164
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
