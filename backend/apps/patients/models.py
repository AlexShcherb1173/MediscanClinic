"""
Models for patients application.

This app stores patient-specific profile data that should not belong to the auth user model.
If you don't need any patient profile fields, consider removing the whole app from INSTALLED_APPS.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class PatientProfile(models.Model):
    """
    Optional patient profile linked 1-to-1 with the auth user.

    Keep only truly patient-related fields here (medical/identity/profile data),
    not login credentials.

    Fields:
        user: One-to-one link to accounts.User
        birth_date: optional date of birth
        notes: optional internal notes (not visible to patient by default)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        verbose_name="Пользователь",
    )
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    notes = models.TextField("Заметки", blank=True)

    class Meta:
        verbose_name = "Профиль пациента"
        verbose_name_plural = "Профили пациентов"

    def __str__(self) -> str:
        return f"PatientProfile: {self.user}"