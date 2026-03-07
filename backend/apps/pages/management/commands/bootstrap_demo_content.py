from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import transaction

from apps.appointments.models import Appointment
from apps.promos.models import Promo
from apps.services.models import Service, ServiceCategory
from apps.staff.models import Doctor


class Command(BaseCommand):
    help = (
        "Bootstrap demo content from fixtures. "
        "Loads fixtures only if the database is empty, unless --force is used."
    )

    base_fixtures = [
        "apps/services/fixtures/services_categories.json",
        "apps/services/fixtures/services.json",
        "apps/staff/fixtures/staff_seed.json",
        "apps/promos/fixtures/promos.json",
    ]

    extra_fixtures = [
        "apps/appointments/fixtures/appointments.json",
        "apps/results/fixtures/research_results.json",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Load fixtures even if demo data already exists.",
        )
        parser.add_argument(
            "--skip-extra",
            action="store_true",
            help="Skip loading appointments and research results fixtures.",
        )

    def handle(self, *args, **options):
        force: bool = options["force"]
        skip_extra: bool = options["skip_extra"]

        if not force and not self._is_database_empty():
            self.stdout.write(
                self.style.WARNING(
                    "Demo content already exists. Nothing was loaded. " "Use --force to load fixtures anyway."
                )
            )
            return

        fixture_paths = [self._fixture_path(rel_path) for rel_path in self.base_fixtures]

        if not skip_extra:
            fixture_paths.extend(self._fixture_path(rel_path) for rel_path in self.extra_fixtures)

        self.stdout.write(self.style.MIGRATE_HEADING("Loading demo fixtures..."))

        for fixture_path in fixture_paths:
            self.stdout.write(f" -> {fixture_path}")
            self._load_fixture(fixture_path)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo content bootstrap completed."))
        self.stdout.write(self._summary())

    def _fixture_path(self, relative_path: str) -> str:
        """
        Convert a fixture path relative to backend/ into an absolute file path.
        Example:
            apps/services/fixtures/services.json
            -> /app/backend/apps/services/fixtures/services.json
        """
        return str(Path(settings.BASE_DIR) / relative_path)

    def _is_database_empty(self) -> bool:
        """
        Consider the project empty if the main showcase/demo tables are empty.
        """
        return (
            ServiceCategory.objects.count() == 0
            and Service.objects.count() == 0
            and Doctor.objects.count() == 0
            and Promo.objects.count() == 0
            and Appointment.objects.count() == 0
        )

    @transaction.atomic
    def _load_fixture(self, fixture_path: str) -> None:
        """
        Load a single fixture inside a transaction.
        """
        call_command("loaddata", fixture_path, verbosity=1)

    def _summary(self) -> str:
        return (
            f"ServiceCategory: {ServiceCategory.objects.count()}\n"
            f"Service: {Service.objects.count()}\n"
            f"Doctor: {Doctor.objects.count()}\n"
            f"Promo: {Promo.objects.count()}\n"
            f"Appointment: {Appointment.objects.count()}"
        )
