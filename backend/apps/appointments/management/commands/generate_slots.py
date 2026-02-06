from __future__ import annotations

from datetime import datetime, timedelta, time
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.services.models import Service
from apps.appointments.models import AppointmentSlot


def daterange(start_date, days: int) -> Iterable:
    for i in range(days):
        yield start_date + timedelta(days=i)


class Command(BaseCommand):
    help = "Generate AppointmentSlot for active services for N days ahead."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14, help="How many days ahead to generate (default: 14)")
        parser.add_argument("--step", type=int, default=20, help="Slot step in minutes (default: 20)")
        parser.add_argument("--start", type=str, default="08:00", help="Workday start HH:MM (default: 08:00)")
        parser.add_argument("--end", type=str, default="20:00", help="Workday end HH:MM (default: 20:00)")
        parser.add_argument("--service", type=int, default=None, help="Only for one service_id")
        parser.add_argument("--dry-run", action="store_true", help="Do not write to DB, only show stats")

    def handle(self, *args, **opts):
        days: int = opts["days"]
        step_min: int = opts["step"]
        start_str: str = opts["start"]
        end_str: str = opts["end"]
        service_id: int | None = opts["service"]
        dry_run: bool = opts["dry_run"]

        try:
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))
            start_t = time(start_h, start_m)
            end_t = time(end_h, end_m)
        except Exception:
            self.stderr.write(self.style.ERROR("Invalid --start/--end format. Use HH:MM"))
            return

        if step_min <= 0 or step_min > 240:
            self.stderr.write(self.style.ERROR("Invalid --step minutes"))
            return

        # услуги
        services_qs = Service.objects.filter(is_active=True, category__is_active=True)
        if service_id:
            services_qs = services_qs.filter(id=service_id)

        services = list(services_qs)
        if not services:
            self.stderr.write(self.style.WARNING("No active services found (or wrong --service id)."))
            return

        tz = timezone.get_current_timezone()
        today = timezone.localdate()

        created = 0
        skipped_existing = 0

        def iter_times(day_date):
            start_dt = timezone.make_aware(datetime.combine(day_date, start_t), tz)
            end_dt = timezone.make_aware(datetime.combine(day_date, end_t), tz)
            step = timedelta(minutes=step_min)

            cur = start_dt
            while cur < end_dt:
                yield cur, cur + step
                cur += step

        # основной проход
        # чтобы не долбить БД по одному слоту, соберём существующие пары (service_id, starts_at)
        # для диапазона дат и только нужных услуг
        start_dt_all = timezone.make_aware(datetime.combine(today, time(0, 0)), tz)
        end_dt_all = start_dt_all + timedelta(days=days + 1)

        existing = set(
            AppointmentSlot.objects.filter(
                service_id__in=[s.id for s in services],
                starts_at__gte=start_dt_all,
                starts_at__lt=end_dt_all,
            ).values_list("service_id", "starts_at")
        )

        to_create: list[AppointmentSlot] = []

        for day in daterange(today, days):
            for service in services:
                for starts_at, ends_at in iter_times(day):
                    key = (service.id, starts_at)
                    if key in existing:
                        skipped_existing += 1
                        continue

                    to_create.append(
                        AppointmentSlot(
                            service=service,
                            starts_at=starts_at,
                            ends_at=ends_at,
                            is_active=True,
                            is_booked=False,
                        )
                    )
                    created += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN (no DB changes)"))
            self.stdout.write(f"Would create: {created}")
            self.stdout.write(f"Skipped existing: {skipped_existing}")
            return

        if not to_create:
            self.stdout.write(self.style.SUCCESS("Nothing to create. All slots already exist."))
            return

        with transaction.atomic():
            AppointmentSlot.objects.bulk_create(to_create, batch_size=2000)

        self.stdout.write(self.style.SUCCESS("Slots generated successfully."))
        self.stdout.write(f"Created: {created}")
        self.stdout.write(f"Skipped existing: {skipped_existing}")
        self.stdout.write(f"Services: {len(services)} | Days: {days} | Step: {step_min} min | {start_str}-{end_str}")