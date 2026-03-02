"""
Команда управления для генерации слотов записи на приём.
Создаёт объекты AppointmentSlot для каждой активной услуги
(и только если категория услуги тоже активна) на N дней вперёд,
в указанном временном диапазоне, с фиксированным шагом (в минутах).
Пример:
    python manage.py generate_slots --days 14 --start 08:00 --end 20:00 --step 20 --replace
Примечания:
    - Если в модели AppointmentSlot нет уникального ограничения
      (например, service + starts_at), то повторные запуски без --replace
      могут создавать дубликаты.
    - Для ускорения используется bulk_create пакетами (батчами),
      чтобы снизить нагрузку на базу данных.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.appointments.models import AppointmentSlot
from apps.services.models import Service


class Command(BaseCommand):
    """
    Генерирует слоты AppointmentSlot для активных услуг.
    Параметры:
        --days: на сколько дней вперёд генерировать (по умолчанию 14)
        --start: время начала дня в формате HH:MM (по умолчанию 08:00)
        --end: время окончания дня в формате HH:MM (по умолчанию 20:00)
        --step: длительность/шаг слота в минутах (по умолчанию 20)
        --replace: удалить слоты в генерируемом диапазоне дат перед созданием
        --dry-run: показать план и выйти без изменений
    """

    help = "Generate AppointmentSlot for each active service (08:00-20:00, step 20 min) for N days вперед."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=14, help="How many days вперед (default: 14)"
        )
        parser.add_argument(
            "--start",
            type=str,
            default="08:00",
            help="Day start HH:MM (default: 08:00)",
        )
        parser.add_argument(
            "--end", type=str, default="20:00", help="Day end HH:MM (default: 20:00)"
        )
        parser.add_argument(
            "--step", type=int, default=20, help="Step in minutes (default: 20)"
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing generated range first",
        )
        parser.add_argument("--dry-run", action="store_true", help="Only show counts")

    def handle(self, *args, **options):
        """
        Точка входа выполнения команды.

        Алгоритм:
            1) Считывает и валидирует параметры (--days, --start, --end, --step).
            2) Определяет список активных услуг (и активных категорий).
            3) Рассчитывает планируемое количество слотов.
            4) При --dry-run выводит план и завершает работу.
            5) При --replace удаляет слоты в указанном диапазоне дат.
            6) Создаёт слоты пакетами через bulk_create(ignore_conflicts=True).
        """
        days: int = options["days"]
        step_min: int = options["step"]
        start_s: str = options["start"]
        end_s: str = options["end"]
        replace: bool = options["replace"]
        dry_run: bool = options["dry_run"]

        try:
            sh, sm = map(int, start_s.split(":"))
            eh, em = map(int, end_s.split(":"))
            day_start = time(sh, sm)
            day_end = time(eh, em)
        except Exception:
            self.stderr.write(self.style.ERROR("Bad --start/--end format. Use HH:MM"))
            return

        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        date_from = today
        date_to = today + timedelta(days=days)  # non-inclusive end

        service_ids = list(
            Service.objects.filter(
                is_active=True, category__is_active=True
            ).values_list("id", flat=True)
        )
        if not service_ids:
            self.stderr.write(self.style.WARNING("No active services found."))
            return

        # Кол-во слотов в одном дне: start включительно, end не включительно (t < end)
        dummy_start = datetime.combine(today, day_start)
        dummy_start = datetime.combine(today, day_start)
        dummy_end = datetime.combine(today, day_end)
        per_day = 0
        cur = dummy_start
        while cur < dummy_end:
            per_day += 1
            cur += timedelta(minutes=step_min)

        total_planned = len(service_ids) * days * per_day
        self.stdout.write(f"Active services: {len(service_ids)}")
        self.stdout.write(f"Days: {days} ({date_from}..{date_to})")
        self.stdout.write(
            f"Per day slots: {per_day} ({start_s}..{end_s}, step {step_min}m)"
        )
        self.stdout.write(f"Planned total: {total_planned}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: no changes made."))
            return

        with transaction.atomic():
            if replace:
                deleted, _ = AppointmentSlot.objects.filter(
                    starts_at__date__gte=date_from,
                    starts_at__date__lt=date_to,
                ).delete()
                self.stdout.write(
                    self.style.WARNING(f"Deleted: {deleted} objects in range")
                )

            created = 0
            skipped = 0
            batch: list[AppointmentSlot] = []

            for day_offset in range(days):
                day = date_from + timedelta(days=day_offset)

                start_dt = timezone.make_aware(datetime.combine(day, day_start), tz)
                end_dt = timezone.make_aware(datetime.combine(day, day_end), tz)

                t = start_dt
                while t < end_dt:
                    slot_end = t + timedelta(minutes=step_min)

                    for service_id in service_ids:
                        batch.append(
                            AppointmentSlot(
                                service_id=service_id,
                                starts_at=t,
                                ends_at=slot_end,
                                is_active=True,
                                is_booked=False,
                            )
                        )

                    t += timedelta(minutes=step_min)

                    # Сбрасываем батч, чтобы не раздувать память
                    if len(batch) >= 5000:
                        res = AppointmentSlot.objects.bulk_create(
                            batch, ignore_conflicts=True
                        )
                        created += len(res)
                        skipped += len(batch) - len(res)
                        batch = []

            if batch:
                res = AppointmentSlot.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(res)
                skipped += len(batch) - len(res)

        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped duplicates: {skipped}"))
