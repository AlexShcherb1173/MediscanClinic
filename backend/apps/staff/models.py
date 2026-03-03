"""
Модели приложения персонала (staff).
Содержит:
- Specialty — медицинская специализация;
- Doctor — профиль врача с фотографией и специализациями;
- DoctorSchedule — недельные интервалы приёма врача.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class Specialty(models.Model):
    """
    Модель медицинской специализации.
    Пример:
        «Кардиолог», «Врач УЗИ», «Невролог».
    Используется для группировки врачей
    и фильтрации по направлениям.
    """

    name = models.CharField("Специальность", max_length=120)

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ("name",)

    def __str__(self) -> str:
        """
        Возвращает название специализации
        для отображения в админке и интерфейсе.
        """
        return self.name


class Doctor(models.Model):
    """
    Модель врача.
    Содержит основные данные профиля врача,
    используемые для отображения на сайте.
    Поля:
        full_name: ФИО врача.
        photo: Фото (опционально).
        specialties: Связанные специализации (many-to-many).
        bio: Краткая биография или описание.
        experience_years: Стаж работы (в годах).
        is_active: Флаг отображения врача на сайте.
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
        """
        Возвращает ФИО врача
        для отображения в админке и списках.
        """
        return self.full_name


class DoctorSchedule(models.Model):
    """
    Модель недельного расписания врача.
    Каждая запись описывает один временной интервал
    в конкретный день недели (например, понедельник 09:00–13:00).
    Используется для формирования доступных слотов записи.
    Бизнес-правило:
        время окончания (time_to) должно быть строго больше времени начала (time_from).
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
        Валидация временного интервала расписания.
        Проверяет, что:
            - time_from и time_to заданы;
            - time_to > time_from.
        При нарушении выбрасывает ValidationError.
        """
        super().clean()
        if self.time_from and self.time_to and self.time_to <= self.time_from:
            raise ValidationError({"time_to": "Время 'До' должно быть позже времени 'С'."})

    def __str__(self) -> str:
        """
        Возвращает человекочитаемое представление расписания
        в формате:
            <Врач> — <День недели> <С>-<До>
        """
        return f"{self.doctor} — {self.get_weekday_display()} {self.time_from}-{self.time_to}"
