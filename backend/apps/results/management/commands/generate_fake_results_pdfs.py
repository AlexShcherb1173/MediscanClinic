"""
Management command to generate demo PDF files for ResearchResult.

The command creates PDF files inside MEDIA_ROOT under:
    results/user_<patient_id>/<filename>

It does NOT create ResearchResult DB rows — only files.
Useful for demo content and fixtures.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _make_pdf(path: Path, title: str, patient_id: int, lines: list[str]) -> None:
    """
    Generate a simple one-page (or multi-page) PDF file.

    Args:
        path: Absolute file path where PDF should be written.
        title: PDF document title (used as metadata and printed in body).
        patient_id: Patient identifier printed in body.
        lines: Bullet lines rendered in the PDF body.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4  # noqa: F841 (width not used, kept for clarity)

    c.setTitle(title)
    c.setAuthor("MediscanClinic (demo generator)")

    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Mediscan — Результат исследования (DEMO)")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"Пациент ID: {patient_id}")
    y -= 18
    c.drawString(40, y, f"Документ: {title}")
    y -= 24

    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(40, y, f"• {line}")
        y -= 16
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    c.showPage()
    c.save()


# Demo files to generate: (patient_id, filename, title, bullet_lines)
FILES: list[tuple[int, str, str, list[str]]] = [
    # user 1
    (1, "sample3.pdf", "Общий анализ крови", ["Показатели: в норме", "Рекомендация: контроль через 6 мес."]),
    (1, "sample2.pdf", "МРТ поясничного отдела", ["Протрузия L4-L5", "Без признаков секвестрации"]),
    (
        1,
        "sample1.pdf",
        "Биохимический анализ крови",
        ["Холестерин: повышен", "Рекомендация: диета / консультация врача"],
    ),
    # user 2
    (2, "sample3.pdf", "Общий анализ крови", ["Показатели: в норме", "Рекомендация: контроль через 6 мес."]),
    (2, "sample2.pdf", "МРТ поясничного отдела", ["Протрузия L4-L5", "Без признаков секвестрации"]),
    (
        2,
        "sample1.pdf",
        "Биохимический анализ крови",
        ["Холестерин: повышен", "Рекомендация: диета / консультация врача"],
    ),
    # user 3
    (3, "cbc_u3.pdf", "Общий анализ крови", ["Лейкоциты: норма", "Гемоглобин: норма"]),
    (3, "us_u3.pdf", "УЗИ брюшной полости", ["Без особенностей", "Печень: без структурных изменений"]),
    (
        3,
        "thyroid_u3.pdf",
        "УЗИ щитовидной железы",
        ["Узел 4 мм (наблюдение)", "Рекомендация: контроль через 12 мес."],
    ),
]


class Command(BaseCommand):
    """Generate demo PDFs inside MEDIA_ROOT for a few demo patient ids."""

    help = "Generate demo PDFs in MEDIA_ROOT for results/user_<id>/..."

    def handle(self, *args, **options):
        """Generate PDFs and print created relative paths."""
        media_root = Path(settings.MEDIA_ROOT)

        for patient_id, filename, title, lines in FILES:
            rel = Path("results") / f"user_{patient_id}" / filename
            abs_path = media_root / rel
            _make_pdf(abs_path, title=title, patient_id=patient_id, lines=lines)
            self.stdout.write(self.style.SUCCESS(f"Created: {rel}"))

        self.stdout.write(self.style.SUCCESS("Done."))