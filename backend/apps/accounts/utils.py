"""
Utilities for accounts application.
"""

from __future__ import annotations


def normalize_phone(phone: str) -> str:
    """
    Normalize phone to digits-only string.

    Examples:
        +7(985) 698-72-82 -> 79856987282
        8 985 698-72-82   -> 89856987282
    """
    return "".join(ch for ch in (phone or "") if ch.isdigit())