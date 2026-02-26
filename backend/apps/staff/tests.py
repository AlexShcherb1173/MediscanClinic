from __future__ import annotations

from datetime import time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from apps.staff.models import Doctor, Specialty, DoctorSchedule
from apps.staff.utils import generate_time_slots
from apps.staff.context_processors import doctor_slider_items


class StaffModelsTests(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="Кардиолог")
        self.doctor = Doctor.objects.create(
            full_name="Иван Иванов",
            bio="Опытный врач",
            experience_years=10,
            is_active=True,
        )
        self.doctor.specialties.add(self.specialty)

    def test_specialty_str(self):
        self.assertEqual(str(self.specialty), "Кардиолог")

    def test_doctor_str(self):
        self.assertEqual(str(self.doctor), "Иван Иванов")

    def test_doctor_schedule_str(self):
        schedule = DoctorSchedule.objects.create(
            doctor=self.doctor,
            weekday=0,
            time_from=time(9, 0),
            time_to=time(12, 0),
        )
        s = str(schedule)
        self.assertIn("Иван Иванов", s)
        self.assertIn("Понедельник", s)
        self.assertIn("09:00", s)


class StaffViewsTests(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="Невролог")
        self.doctor = Doctor.objects.create(
            full_name="Анна Петрова",
            bio="Специалист",
            experience_years=5,
            is_active=True,
        )
        self.doctor.specialties.add(self.specialty)

    def test_doctor_list_view(self):
        url = reverse("staff:doctor_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Анна Петрова")
        self.assertIn("doctors", response.context)

    def test_doctor_detail_view_groups_schedule(self):
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            weekday=1,
            time_from=time(10, 0),
            time_to=time(13, 0),
        )
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            weekday=1,
            time_from=time(15, 0),
            time_to=time(18, 0),
        )

        url = reverse("staff:doctor_detail", args=[self.doctor.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("schedules", response.context)

        schedules = response.context["schedules"]
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0]["weekday"], 1)
        self.assertEqual(len(schedules[0]["windows"]), 2)

    def test_doctor_detail_only_active(self):
        inactive = Doctor.objects.create(
            full_name="Неактивный врач",
            is_active=False,
        )
        url = reverse("staff:doctor_detail", args=[inactive.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class StaffContextProcessorTests(TestCase):
    @patch("apps.staff.models.Doctor.objects")
    def test_doctor_slider_items_returns_dict(self, mock_manager):
        """
        Проверяем, что возвращается dict, а не tuple.
        """

        class DummyPhoto:
            url = "/media/doctors/test.jpg"

        class DummyDoctor:
            id = 1
            full_name = "Доктор Тест"
            photo = DummyPhoto()

        mock_qs = [DummyDoctor()]
        mock_manager.filter.return_value.exclude.return_value.only.return_value.order_by.return_value.__getitem__.return_value = mock_qs

        result = doctor_slider_items(None)
        self.assertIsInstance(result, dict)
        self.assertIn("doctor_slider_items", result)
        self.assertEqual(result["doctor_slider_items"][0]["name"], "Доктор Тест")


class StaffUtilsTests(TestCase):
    def test_generate_time_slots(self):
        slots = generate_time_slots(time(9, 0), time(10, 0), step_minutes=20)
        self.assertEqual(len(slots), 3)
        self.assertEqual(slots[0], time(9, 0))
        self.assertEqual(slots[1], time(9, 20))
        self.assertEqual(slots[2], time(9, 40))

    def test_generate_time_slots_end_exclusive(self):
        slots = generate_time_slots(time(9, 0), time(9, 30), step_minutes=30)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0], time(9, 0))