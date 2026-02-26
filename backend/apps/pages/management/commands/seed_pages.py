"""
Management command to seed default static Page records.

Creates or updates a set of predefined pages (about-*) with HTML content.
The command is idempotent: it can be executed multiple times safely.
"""

from django.core.management.base import BaseCommand

from apps.pages.models import Page


TEMPLATES = {
    "about-history": {
        "title": "История Mediscan",
        "content": """
<div class="prose max-w-none">
  <h1>История Mediscan</h1>
  <p><strong>Mediscan</strong> — сервис, который делает запись и выбор услуг понятными и быстрыми.</p>

  <h2>Коротко</h2>
  <ul>
    <li>каталог услуг с описаниями;</li>
    <li>онлайн-запись по слотам;</li>
    <li>подтверждения и напоминания.</li>
  </ul>

  <div class="not-prose rounded-2xl border border-slate-200 bg-white p-4">
    <div class="font-semibold">Подсказка</div>
    <div class="text-sm text-slate-600 mt-1">
      Этот текст — шаблон. Замените на реальную историю компании.
    </div>
  </div>
</div>
""".strip(),
    },
    "about-mission": {
        "title": "Миссия",
        "content": """
<div class="prose max-w-none">
  <h1>Миссия</h1>
  <p>
    Наша миссия — сделать медицинскую диагностику понятной, доступной и спокойной:
    без сложных терминов, очередей и неопределённости.
  </p>

  <h2>Принципы</h2>
  <ul>
    <li><strong>Прозрачность</strong> — понятные услуги, цены, подготовка.</li>
    <li><strong>Сервис</strong> — подтверждение записи и поддержка.</li>
    <li><strong>Безопасность</strong> — бережная работа с персональными данными.</li>
  </ul>

  <div class="not-prose grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="font-semibold">Пациент</div>
      <div class="text-sm text-slate-600 mt-1">Ставим удобство пациента на первое место.</div>
    </div>
    <div class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="font-semibold">Качество</div>
      <div class="text-sm text-slate-600 mt-1">Следуем стандартам и контролю процессов.</div>
    </div>
    <div class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="font-semibold">Технологии</div>
      <div class="text-sm text-slate-600 mt-1">Автоматизируем запись и коммуникации.</div>
    </div>
  </div>
</div>
""".strip(),
    },
    "about-quality": {
        "title": "Качество",
        "content": """
<div class="prose max-w-none">
  <h1>Качество</h1>
  <p>
    Мы выстраиваем процессы так, чтобы пациент получал стабильный результат:
    понятную услугу, корректную подготовку и аккуратное сопровождение.
  </p>

  <h2>Как мы контролируем качество</h2>
  <ul>
    <li>регламенты и чек-листы;</li>
    <li>контроль расписания и слотов;</li>
    <li>поддержка и обратная связь;</li>
    <li>обновление описаний услуг и памяток.</li>
  </ul>

  <div class="not-prose rounded-2xl border border-sky-200 bg-sky-50 p-4">
    <div class="font-semibold text-sky-900">Важно</div>
    <div class="text-sm text-sky-900 mt-1">
      Этот раздел можно дополнить реальными документами и стандартами клиники.
    </div>
  </div>
</div>
""".strip(),
    },
    "about-licenses": {
        "title": "Лицензии",
        "content": """
<div class="prose max-w-none">
  <h1>Лицензии</h1>
  <p>
    Здесь размещается информация о лицензиях и разрешительных документах.
    Можно добавить номера, даты, ссылки на сканы, адреса филиалов.
  </p>

  <h2>Документы</h2>
  <ul>
    <li>Лицензия на медицинскую деятельность — № ____ от ____</li>
    <li>Санитарно-эпидемиологическое заключение — № ____ от ____</li>
    <li>Сведения о юр. лице и адресах — ____</li>
  </ul>

  <div class="not-prose rounded-2xl border border-slate-200 bg-white p-4">
    <div class="font-semibold">Сканы</div>
    <div class="text-sm text-slate-600 mt-1">
      Если сканы будут в медиа — добавьте ссылки или вставьте изображения в HTML.
    </div>
  </div>
</div>
""".strip(),
    },
}
"""
Mapping of page slugs to template data for seeding.

Each item provides:
- title: page title
- content: HTML content (Tailwind + prose classes recommended)
"""


class Command(BaseCommand):
    """
    Seed default CMS-like pages.

    The command creates or updates Page objects based on the `TEMPLATES` mapping.
    """

    help = "Create/update default Pages templates (about-*)"

    def handle(self, *args, **options):
        """
        Execute the command.

        For each slug in `TEMPLATES`:
        - create a Page if it does not exist
        - otherwise update its fields

        Prints a summary of created/updated objects.
        """
        created = 0
        updated = 0

        for slug, data in TEMPLATES.items():
            _, is_created = Page.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": data["title"],
                    "content": data["content"],
                    "is_published": True,
                },
            )
            created += int(is_created)
            updated += int(not is_created)

        self.stdout.write(
            self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}")
        )