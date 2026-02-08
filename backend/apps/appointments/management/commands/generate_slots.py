from __future__ import annotations

from datetime import datetime, timedelta, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.services.models import Service
from apps.appointments.models import AppointmentSlot


class Command(BaseCommand):
    help = "Generate AppointmentSlot for each active service (08:00-20:00, step 20 min) for N days вперед."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="How many days вперед (default: 14)")
        parser.add_argument("--start", type=str, default="08:00", help="Day start HH:MM (default: 08:00)")
        parser.add_argument("--end", type=str, default="20:00", help="Day end HH:MM (default: 20:00)")
        parser.add_argument("--step", type=int, default=20, help="Step in minutes (default: 20)")
        parser.add_argument("--replace", action="store_true", help="Delete existing generated range first")
        parser.add_argument("--dry-run", action="store_true", help="Only show counts")

    def handle(self, *args, **options):
        days = options["days"]
        step_min = options["step"]
        start_s = options["start"]
        end_s = options["end"]
        replace = options["replace"]
        dry_run = options["dry_run"]

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
        date_to = today + timedelta(days=days)  # не включая

        services = Service.objects.filter(is_active=True, category__is_active=True).only("id")
        if not services.exists():
            self.stderr.write(self.style.WARNING("No active services found."))
            return

        # посчитаем сколько слотов на день
        # слоты создаём начиная с start, пока starts_at < end
        dummy_start = datetime.combine(today, day_start)
        dummy_end = datetime.combine(today, day_end)
        per_day = 0
        cur = dummy_start
        while cur < dummy_end:
            per_day += 1
            cur += timedelta(minutes=step_min)

        total_planned = services.count() * days * per_day
        self.stdout.write(f"Active services: {services.count()}")
        self.stdout.write(f"Days: {days} ({date_from}..{date_to})")
        self.stdout.write(f"Per day slots: {per_day} ({start_s}..{end_s}, step {step_min}m)")
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
                self.stdout.write(self.style.WARNING(f"Deleted: {deleted} objects in range"))

            created = 0
            skipped = 0

            # Чтобы не падать на дублях — делаем bulk + ignore_conflicts (если есть unique constraint)
            batch = []

            for day_offset in range(days):
                day = date_from + timedelta(days=day_offset)

                start_dt = timezone.make_aware(datetime.combine(day, day_start), tz)
                end_dt = timezone.make_aware(datetime.combine(day, day_end), tz)

                t = start_dt
                while t < end_dt:
                    slot_end = t + timedelta(minutes=step_min)
                    for s in services:
                        batch.append(
                            AppointmentSlot(
                                service_id=s.id,
                                starts_at=t,
                                ends_at=slot_end,
                                is_active=True,
                                is_booked=False,
                            )
                        )
                    t += timedelta(minutes=step_min)

                    # flush batch чтобы память не росла
                    if len(batch) >= 5000:
                        res = AppointmentSlot.objects.bulk_create(batch, ignore_conflicts=True)
                        created += len(res)
                        skipped += (len(batch) - len(res))
                        batch = []

            if batch:
                res = AppointmentSlot.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(res)
                skipped += (len(batch) - len(res))

        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped duplicates: {skipped}"))