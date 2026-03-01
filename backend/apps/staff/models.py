"""
Models for staff application.

Contains:
- Specialty: medical specialization
- Doctor: doctor profile with photo and specialties
- DoctorSchedule: weekly availability windows for each doctor
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class Specialty(models.Model):
    """
    Medical specialty (e.g., "Cardiologist", "Ultrasound doctor").
    """

    name = models.CharField("Специальность", max_length=120)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ("name",)

    def __str__(self) -> str:
        """Return specialty name for admin/UI."""
        return self.name


class Doctor(models.Model):
    """
    Doctor profile.

    Attributes:
        full_name: doctor's full name
        photo: optional portrait photo
        specialties: many-to-many relation to specialties
        bio: optional biography/description
        experience_years: years of experience (non-negative)
        is_active: controls visibility on website
    """

    full_name = models.CharField("ФИО", max_length=150)
    photo = models.ImageField("Фото", upload_to="doctors/", blank=True)
    specialties = models.ManyToManyField(
        Specialty,
        related_name="doctors",
        verbose_name="Специальности",
        blank=True,
    )
    bio = models.TextField("Биография", blank=True)
    experience_years = models.PositiveIntegerField("Стаж (лет)", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"
        ordering = ("full_name",)

    def __str__(self) -> str:
        """Return full name for admin/UI."""
        return self.full_name


class DoctorSchedule(models.Model):
    """
    Weekly schedule window for a doctor.

    Each record defines one time window for a weekday:
    e.g. Monday 09:00–13:00.

    Validation:
        time_to must be greater than time_from.
    """

    WEEKDAYS = (
        (0, "Понедельник"),
        (1, "Вторник"),
        (2, "Среда"),
        (3, "Четверг"),
        (4, "Пятница"),
        (5, "Суббота"),
        (6, "Воскресенье"),
    )

    doctor = models.ForeignKey(
        Doctor,
        related_name="schedules",
        on_delete=models.CASCADE,
        verbose_name="Врач",
    )
    weekday = models.PositiveSmallIntegerField("День недели", choices=WEEKDAYS)
    time_from = models.TimeField("С")
    time_to = models.TimeField("До")

    class Meta:
        verbose_name = "Расписание врача"
        verbose_name_plural = "Расписания врачей"
        ordering = ("doctor", "weekday", "time_from")

    def clean(self) -> None:
        """
        Validate schedule window.

        Ensures end time is strictly after start time.
        """
        super().clean()
        if self.time_from and self.time_to and self.time_to <= self.time_from:
            raise ValidationError(
                {"time_to": "Время 'До' должно быть позже времени 'С'."}
            )

    def __str__(self) -> str:
        """Return human-readable schedule string."""
        return f"{self.doctor} — {self.get_weekday_display()} {self.time_from}-{self.time_to}"
