from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.cabinet.context_processors import cabinet_badges
from apps.results.models import ResearchResult

User = get_user_model()


class CabinetAuthViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990001234", password="123456", full_name="User")

    def test_dashboard_requires_login(self):
        url = reverse("cabinet:dashboard")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_appointments_requires_login(self):
        url = reverse("cabinet:appointments")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_results_requires_login(self):
        url = reverse("cabinet:results")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_dashboard_ok_for_logged_in(self):
        self.client.force_login(self.user)
        url = reverse("cabinet:dashboard")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("last_appointments", r.context)
        self.assertIn("last_results", r.context)

    def test_appointments_ok_for_logged_in(self):
        self.client.force_login(self.user)
        url = reverse("cabinet:appointments")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("appointments", r.context)

    def test_results_ok_for_logged_in(self):
        self.client.force_login(self.user)
        url = reverse("cabinet:results")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("results", r.context)


class CabinetContextProcessorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990009999", password="123456", full_name="User")

    def test_badges_anonymous(self):
        class DummyReq:
            user = type("U", (), {"is_authenticated": False})()

        out = cabinet_badges(DummyReq())
        self.assertEqual(out["unread_results_count"], 0)

    def test_badges_authenticated_returns_int(self):
        # Без ResearchResult данных просто проверяем что не падает и возвращает int
        class DummyReq:
            user = self.user

        out = cabinet_badges(DummyReq())
        self.assertIn("unread_results_count", out)
        self.assertIsInstance(out["unread_results_count"], int)

class CabinetViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990001234", password="123456", full_name="User")
        self.other = User.objects.create_user(phone="79990001235", password="123456", full_name="Other")

    def test_dashboard_requires_login(self):
        url = reverse("cabinet:dashboard")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_results_marks_unread_as_viewed(self):
        # 2 unread for self.user, 1 unread for other
        r1 = ResearchResult.objects.create(patient=self.user, title="R1", is_viewed=False)
        r2 = ResearchResult.objects.create(patient=self.user, title="R2", is_viewed=False)
        ResearchResult.objects.create(patient=self.other, title="R_other", is_viewed=False)

        self.client.force_login(self.user)
        url = reverse("cabinet:results")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        r1.refresh_from_db()
        r2.refresh_from_db()
        self.assertTrue(r1.is_viewed)
        self.assertTrue(r2.is_viewed)
        self.assertIsNotNone(r1.viewed_at)
        self.assertIsNotNone(r2.viewed_at)

    def test_context_processor_badges_counts_unread(self):
        ResearchResult.objects.create(patient=self.user, title="R1", is_viewed=False)
        ResearchResult.objects.create(patient=self.user, title="R2", is_viewed=True)
        ResearchResult.objects.create(patient=self.user, title="R3", is_viewed=False)

        class DummyReq:
            user = self.user

        out = cabinet_badges(DummyReq())
        self.assertEqual(out["unread_results_count"], 2)

    def test_context_processor_badges_anonymous(self):
        class DummyReq:
            user = type("U", (), {"is_authenticated": False})()

        out = cabinet_badges(DummyReq())
        self.assertEqual(out["unread_results_count"], 0)