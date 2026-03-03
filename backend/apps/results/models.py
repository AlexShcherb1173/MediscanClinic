"""
Модели приложения результатов исследований (results).
Хранит файлы результатов (PDF), привязанные к пациенту (User).
Особенности:
- детерминированный путь загрузки файлов по пациенту;
- защита от коллизий имён файлов;
- отслеживание факта просмотра результата (is_viewed / viewed_at).
"""

from __future__ import annotations

import os
import uuid

from django.conf import settings
from django.db import models


def result_upload_to(instance, filename: str) -> str:
    """
    Формирует путь загрузки файла результата исследования.
    Файл сохраняется в директории:
        results/user_<patient_id>/<uuid>.<ext>
    Логика:
        - исходное имя файла не используется (в целях безопасности);
        - генерируется уникальное имя на основе uuid4;
        - сохраняется оригинальное расширение файла.
    Это:
        - предотвращает конфликты имён;
        - исключает небезопасные названия;
        - группирует файлы по пациентам.
    """
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"results/user_{instance.patient_id}/{safe_name}"


class ResearchResult(models.Model):
    """
    Модель результата исследования пациента.
    Используется для хранения PDF-файлов исследований
    и отслеживания их просмотра пациентом.
    Поля:
        patient: Владелец результата (AUTH_USER_MODEL).
        title: Название исследования (например, «МРТ головного мозга»).
        result_date: Дата проведения исследования.
        file: PDF-файл результата (временно допускает NULL).
        comment: Внутренний комментарий.
        is_viewed: Флаг просмотра пациентом.
        viewed_at: Дата и время первого просмотра.
        created_at: Дата загрузки результата в систему.
    """

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_results",
        verbose_name="Пациент",
    )

    title = models.CharField("Название", max_length=255)
    result_date = models.DateField("Дата исследования", null=True, blank=True)

    # временно nullable: пока не очищены NULL в БД
    file = models.FileField(
        "Файл (PDF)",
        upload_to=result_upload_to,
        null=True,
        blank=True,
    )

    comment = models.TextField("Комментарий", blank=True)

    is_viewed = models.BooleanField("Просмотрено", default=False)
    viewed_at = models.DateTimeField("Просмотрено в", null=True, blank=True)

    created_at = models.DateTimeField("Загружено", auto_now_add=True)

    class Meta:
        ordering = ("-result_date", "-created_at")
        verbose_name = "Результат исследования"
        verbose_name_plural = "Результаты исследований"

    def __str__(self) -> str:
        """
        Строковое представление результата
        для отображения в админке и интерфейсе.
        """
        return f"{self.patient} — {self.title}"
        return f"{self.patient} — {self.title}"
