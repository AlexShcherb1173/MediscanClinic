"""
Management-команда для генерации демонстрационных PDF-файлов
результатов исследова
Команда создаёт PDF-файлы внутри MEDIA_ROOT по пути:
    results/user_<patient_id>/<filename>
⚠ Важно:
- объекты ResearchResult в базе данных НЕ создаются;
- создаются только физические PDF-файлы;
- используется для демо-контента, тестов и наполнения стенда.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _make_pdf(path: Path, title: str, patient_id: int, lines: list[str]) -> None:
    """
    Сгенерировать PDF-файл с демонстрационным содержимым.
    Файл создаётся (с промежуточными директориями при необходимости)
    и содержит заголовок, идентификатор пациента и список пунктов.
    Параметры:
        path: Абсолютный путь к создаваемому PDF-файлу.
        title: Название документа (используется в метаданных и в теле PDF).
        patient_id: Идентификатор пациента, отображаемый в документе.
        lines: Список строк, выводимых как пункты (bullet list).
    Особенности:
        - поддерживается автоматический перенос на новую страницу;
        - используется reportlab с базовым форматированием.
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


"""
Набор демонстрационных файлов для генерации.
Структура кортежа:
    (patient_id, filename, title, bullet_lines)
Используется командой для создания тестовых PDF-файлов
в директории MEDIA_ROOT/results/user_<id>/.
"""
FILES: list[tuple[int, str, str, list[str]]] = [
    # user 1
    (
        1,
        "sample3.pdf",
        "Общий анализ крови",
        ["Показатели: в норме", "Рекомендация: контроль через 6 мес."],
    ),
    (
        1,
        "sample2.pdf",
        "МРТ поясничного отдела",
        ["Протрузия L4-L5", "Без признаков секвестрации"],
    ),
    (
        1,
        "sample1.pdf",
        "Биохимический анализ крови",
        ["Холестерин: повышен", "Рекомендация: диета / консультация врача"],
    ),
    # user 2
    (
        2,
        "sample3.pdf",
        "Общий анализ крови",
        ["Показатели: в норме", "Рекомендация: контроль через 6 мес."],
    ),
    (
        2,
        "sample2.pdf",
        "МРТ поясничного отдела",
        ["Протрузия L4-L5", "Без признаков секвестрации"],
    ),
    (
        2,
        "sample1.pdf",
        "Биохимический анализ крови",
        ["Холестерин: повышен", "Рекомендация: диета / консультация врача"],
    ),
    # user 3
    (3, "cbc_u3.pdf", "Общий анализ крови", ["Лейкоциты: норма", "Гемоглобин: норма"]),
    (
        3,
        "us_u3.pdf",
        "УЗИ брюшной полости",
        ["Без особенностей", "Печень: без структурных изменений"],
    ),
    (
        3,
        "thyroid_u3.pdf",
        "УЗИ щитовидной железы",
        ["Узел 4 мм (наблюдение)", "Рекомендация: контроль через 12 мес."],
    ),
]


class Command(BaseCommand):
    """
    Management-команда генерации демо-PDF-файлов.
    Создаёт тестовые PDF-документы в MEDIA_ROOT
    для заранее определённых patient_id.
    Предназначена для:
        - наполнения демо-данными;
        - тестирования отображения результатов;
        - подготовки showcase-стенда.
    """

    help = "Generate demo PDFs in MEDIA_ROOT for results/user_<id>/..."

    def handle(self, *args, **options):
        """
        Основная точка входа команды.
        Для каждого элемента из FILES:
            - формируется относительный путь results/user_<id>/;
            - создаётся PDF-файл;
            - выводится сообщение об успешном создании.
        В конце выводится итоговое сообщение "Done.".
        """
        media_root = Path(settings.MEDIA_ROOT)

        for patient_id, filename, title, lines in FILES:
            rel = Path("results") / f"user_{patient_id}" / filename
            abs_path = media_root / rel
            _make_pdf(abs_path, title=title, patient_id=patient_id, lines=lines)
            self.stdout.write(self.style.SUCCESS(f"Created: {rel}"))

        self.stdout.write(self.style.SUCCESS("Done."))
