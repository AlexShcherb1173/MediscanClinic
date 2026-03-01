from __future__ import annotations

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.pages.models import Page


class PagesModelTests(TestCase):
    def test_page_str(self):
        page = Page.objects.create(title="О клинике", slug="about", content="x")
        self.assertEqual(str(page), "О клинике")

    def test_page_save_autogenerates_slug_when_empty(self):
        page = Page(title="Политика конфиденциальности", slug="")
        page.save()

        self.assertTrue(page.slug)  # generated
        self.assertNotIn(" ", page.slug)


class PagesManagementCommandTests(TestCase):
    def test_seed_pages_command_creates_pages(self):
        call_command("seed_pages")

        self.assertTrue(Page.objects.filter(slug="about-history").exists())
        self.assertTrue(Page.objects.filter(slug="about-mission").exists())
        self.assertTrue(Page.objects.filter(slug="about-quality").exists())
        self.assertTrue(Page.objects.filter(slug="about-licenses").exists())

    def test_seed_pages_command_is_idempotent(self):
        call_command("seed_pages")
        count1 = Page.objects.count()

        call_command("seed_pages")
        count2 = Page.objects.count()

        self.assertEqual(count1, count2)


class PagesViewsTests(TestCase):
    @patch("apps.pages.views.Promo.objects.filter")
    @patch("apps.pages.views.Service.objects.filter")
    @patch("apps.pages.views.Doctor.objects.exclude")
    def test_pages_home_renders_ok(self, doctor_exclude, service_filter, promo_filter):
        """
        Home view should return 200 and provide expected context keys.
        We mock external app querysets to avoid coupling with other apps' models.
        """

        # Promo.objects.filter(...).order_by(... )[:3] -> []
        class _PromoQS:
            def order_by(self, *args, **kwargs):
                return self

            def __getitem__(self, item):
                return []

        promo_filter.return_value = _PromoQS()

        # Service.objects.filter(...).select_related(...).order_by(... )[:4] -> []
        class _ServiceQS:
            def select_related(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def __getitem__(self, item):
                return []

        service_filter.return_value = _ServiceQS()

        # Doctor.objects.exclude(...).exclude(...).only(...).order_by(... )[:10] -> []
        class _DoctorQS:
            def exclude(self, *args, **kwargs):
                return self

            def only(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def __getitem__(self, item):
                return []

        doctor_exclude.return_value = _DoctorQS()

        url = reverse("pages:home")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("promos", resp.context)
        self.assertIn("popular_services", resp.context)
        self.assertIn("doctors_slider", resp.context)

    def test_pages_sitemap_renders_ok(self):
        url = reverse("pages:sitemap")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @patch("apps.pages.views.Doctor.objects.filter")
    def test_page_detail_about_branch_renders_and_has_context(self, doctor_filter):
        """
        slug=about should render custom about template with doctors (and maybe licenses) in context.
        We mock Doctor queryset to avoid DB dependencies.
        """

    def test_page_detail_static_template_slug_renders_ok(self):
        """
        Slug from STATIC_TEMPLATES should render without DB Page record.
        """
        url = reverse("pages:page_detail", kwargs={"slug": "privacy"})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_page_detail_db_page_published_renders_ok(self):
        Page.objects.create(title="FAQ", slug="faq", content="Hello", is_published=True)

        url = reverse("pages:page_detail", kwargs={"slug": "faq"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("page", resp.context)
        self.assertEqual(resp.context["page"].slug, "faq")

    def test_page_detail_db_page_unpublished_returns_404(self):
        Page.objects.create(
            title="Hidden", slug="hidden", content="x", is_published=False
        )

        url = reverse("pages:page_detail", kwargs={"slug": "hidden"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)
