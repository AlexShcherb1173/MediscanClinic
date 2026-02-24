from __future__ import annotations

def normalize_phone(phone: str) -> str:
    """
    Приводим телефон к единому виду: только цифры.
    +7(985) 698-72-82 -> 79856987282
    8 985 698-72-82   -> 89856987282
    """
    return "".join(ch for ch in (phone or "") if ch.isdigit())