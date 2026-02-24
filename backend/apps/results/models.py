import os
import uuid
from django.conf import settings
from django.db import models


def result_upload_to(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"results/user_{instance.patient_id}/{safe_name}"


class ResearchResult(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_results",
        verbose_name="Пациент",
    )

    title = models.CharField("Название", max_length=255)
    result_date = models.DateField("Дата исследования", null=True, blank=True)

    # ⚠ временно оставляем nullable, пока не почистишь NULL в БД
    file = models.FileField(
        "Файл (PDF)",
        upload_to=result_upload_to,
        null=True,
        blank=True,
    )

    comment = models.TextField("Комментарий", blank=True)

    # ⭐ для бейджа "новое"
    is_viewed = models.BooleanField("Просмотрено", default=False)
    viewed_at = models.DateTimeField("Просмотрено в", null=True, blank=True)

    created_at = models.DateTimeField("Загружено", auto_now_add=True)

    class Meta:
        ordering = ("-result_date", "-created_at")
        verbose_name = "Результат исследования"
        verbose_name_plural = "Результаты исследований"

    def __str__(self) -> str:
        return f"{self.patient} — {self.title}"