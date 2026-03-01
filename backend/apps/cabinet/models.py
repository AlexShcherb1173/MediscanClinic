"""
Models for cabinet (personal account) application.

Currently includes:
- UserProfile: per-user extra data (e.g., telegram chat id)
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Extra per-user profile data for personal cabinet.

    Attributes:
        user: one-to-one link to AUTH_USER_MODEL
        telegram_chat_id: optional Telegram chat id for notifications
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    telegram_chat_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self) -> str:
        """Return readable representation for admin."""
        return f"Profile: {self.user}"
