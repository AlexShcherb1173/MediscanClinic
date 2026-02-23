from django.conf import settings
from django.db import models

class ResearchResult(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_results",
        verbose_name="Пациент",
    )

    title = models.CharField("Название", max_length=255)
    result_date = models.DateField("Дата исследования", blank=True, null=True)

    # файл/скан/пдф
    file = models.FileField("Файл результата", upload_to="results/%Y/%m/", blank=True, null=True)

    # текстовая расшифровка (если нужно)
    comment = models.TextField("Комментарий", blank=True)

    created_at = models.DateTimeField("Загружено", auto_now_add=True)

    class Meta:
        ordering = ("-result_date", "-created_at")
        verbose_name = "Результат исследования"
        verbose_name_plural = "Результаты исследований"

    def __str__(self) -> str:
        return f"{self.patient} — {self.title}"