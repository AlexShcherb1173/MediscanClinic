from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.cabinet.models import UserProfile
from apps.results.models import ResearchResult, result_upload_to

User = get_user_model()


class ResultsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990000001", password="123456", full_name="U")

    def test_result_upload_to_contains_patient_id_and_uuid_ext(self):
        rr = ResearchResult(patient=self.user, title="X")
        path = result_upload_to(rr, "report.PDF")
        self.assertIn(f"results/user_{self.user.id}/", path)
        self.assertTrue(path.endswith(".pdf"))


class ResultsViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990000002", password="123456", full_name="U1")
        self.other = User.objects.create_user(phone="79990000003", password="123456", full_name="U2")

    def test_my_results_requires_login(self):
        url = reverse("results:my_results")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_my_results_ok(self):
        self.client.force_login(self.user)
        ResearchResult.objects.create(patient=self.user, title="A")
        ResearchResult.objects.create(patient=self.other, title="B")

        url = reverse("results:my_results")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        qs = r.context["results"]
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "A")

    def test_download_404_for_other_user(self):
        rr = ResearchResult.objects.create(patient=self.other, title="Other")
        url = reverse("results:download", kwargs={"pk": rr.pk})

        self.client.force_login(self.user)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_download_404_when_no_file(self):
        rr = ResearchResult.objects.create(patient=self.user, title="NoFile", file=None)
        url = reverse("results:download", kwargs={"pk": rr.pk})

        self.client.force_login(self.user)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_download_marks_viewed(self):
        rr = ResearchResult.objects.create(patient=self.user, title="PDF")
        rr.file.save("x.pdf", ContentFile(b"%PDF-1.4 test"), save=True)

        url = reverse("results:download", kwargs={"pk": rr.pk})
        self.client.force_login(self.user)
        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        rr.refresh_from_db()
        self.assertTrue(rr.is_viewed)
        self.assertIsNotNone(rr.viewed_at)
        self.assertEqual(r["Content-Type"], "application/pdf")


class ResultsSignalsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="79990000004", password="123456", full_name="U")

    @patch("apps.results.signals.send_telegram_message")
    def test_signal_does_nothing_without_profile_chat_id(self, mocked_send):
        ResearchResult.objects.create(patient=self.user, title="New")
        mocked_send.assert_not_called()

    @patch("apps.results.signals.send_telegram_message")
    def test_signal_sends_when_chat_id_present(self, mocked_send):
        UserProfile.objects.create(user=self.user, telegram_chat_id="123")
        ResearchResult.objects.create(patient=self.user, title="New Result")

        mocked_send.assert_called_once()
        args, kwargs = mocked_send.call_args
        self.assertEqual(args[0], "123")
        self.assertIn("New Result", args[1])


class ResultsManagementCommandTests(TestCase):
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_generate_fake_results_pdfs_creates_files(self):
        """
        Command should create demo PDF files under MEDIA_ROOT/results/user_<id>/...
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                call_command("generate_fake_results_pdfs")

                # a few spot checks (do not overfit to full list)
                p1 = Path(tmpdir) / "results" / "user_1" / "sample1.pdf"
                p2 = Path(tmpdir) / "results" / "user_2" / "sample2.pdf"
                p3 = Path(tmpdir) / "results" / "user_3" / "thyroid_u3.pdf"

                self.assertTrue(p1.exists())
                self.assertTrue(p2.exists())
                self.assertTrue(p3.exists())

                # PDFs should be non-empty
                self.assertGreater(p1.stat().st_size, 100)
                self.assertGreater(p3.stat().st_size, 100)
