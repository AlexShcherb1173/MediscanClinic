from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import transaction

from apps.appointments.models import Appointment, AppointmentSlot
from apps.promos.models import Promo
from apps.services.models import Service, ServiceCategory
from apps.staff.models import Doctor


class Command(BaseCommand):
    """
    Инициализация демо-данных проекта из фикстур.

    Команда:
    - загружает базовые фикстуры, если основная витрина сайта ещё пуста;
    - может дополнительно загрузить appointments/results;
    - может вызвать generate_slots;
    - не выполняет повторную загрузку без явного --force.
    """

    help = (
        "Загружает демо-фикстуры проекта и при необходимости генерирует слоты. "
        "Повторно ничего не делает, если данные уже существуют, если не указан --force."
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

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Принудительно загрузить фикстуры, даже если данные уже существуют.",
        )
        parser.add_argument(
            "--skip-extra",
            action="store_true",
            help="Не загружать appointments.json и research_results.json.",
        )
        parser.add_argument(
            "--with-slots",
            action="store_true",
            help="После загрузки вызвать команду generate_slots.",
        )
        parser.add_argument(
            "--skip-slots-if-exist",
            action="store_true",
            help="Не вызывать generate_slots, если слоты уже существуют.",
        )

    def handle(self, *args, **options) -> None:
        force: bool = options["force"]
        skip_extra: bool = options["skip_extra"]
        with_slots: bool = options["with_slots"]
        skip_slots_if_exist: bool = options["skip_slots_if_exist"]

        self.stdout.write(self.style.MIGRATE_HEADING("Проверка текущего состояния данных..."))
        self.stdout.write(self._summary())

        should_load_fixtures = force or self._is_showcase_empty()

        if should_load_fixtures:
            fixture_paths = [self._fixture_path(rel_path) for rel_path in self.base_fixtures]

            if not skip_extra:
                fixture_paths.extend(self._fixture_path(rel_path) for rel_path in self.extra_fixtures)

            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Загрузка фикстур..."))

            for fixture_path in fixture_paths:
                self.stdout.write(f" -> {fixture_path}")
                self._load_fixture(fixture_path)

            self.stdout.write(self.style.SUCCESS("Фикстуры успешно загружены."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Базовые данные уже существуют. Загрузка фикстур пропущена. "
                    "Используйте --force для принудительной загрузки."
                )
            )

        if with_slots:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Проверка генерации слотов..."))

            if skip_slots_if_exist and AppointmentSlot.objects.exists():
                self.stdout.write(
                    self.style.WARNING("Слоты уже существуют. Генерация пропущена из-за --skip-slots-if-exist.")
                )
            else:
                self.stdout.write(" -> python manage.py generate_slots")
                call_command("generate_slots", verbosity=1)
                self.stdout.write(self.style.SUCCESS("Генерация слотов завершена."))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Bootstrap демо-контента завершён."))
        self.stdout.write(self._summary())

    def _fixture_path(self, relative_path: str) -> str:
        """
        Преобразует путь относительно backend/ в абсолютный путь внутри проекта.
        """
        return str(Path(settings.BASE_DIR) / relative_path)

    def _is_showcase_empty(self) -> bool:
        """
        Считаем витрину пустой, если отсутствуют основные данные,
        от которых зависит отображение сайта.
        """
        return (
            ServiceCategory.objects.count() == 0
            and Service.objects.count() == 0
            and Doctor.objects.count() == 0
            and Promo.objects.count() == 0
        )

    @transaction.atomic
    def _load_fixture(self, fixture_path: str) -> None:
        """
        Загружает одну фикстуру в рамках транзакции.
        """
        call_command("loaddata", fixture_path, verbosity=1)

    def _summary(self) -> str:
        """
        Краткая сводка по ключевым сущностям.
        """
        return (
            f"ServiceCategory: {ServiceCategory.objects.count()}\n"
            f"Service: {Service.objects.count()}\n"
            f"Doctor: {Doctor.objects.count()}\n"
            f"Promo: {Promo.objects.count()}\n"
            f"Appointment: {Appointment.objects.count()}\n"
            f"AppointmentSlot: {AppointmentSlot.objects.count()}"
        )
