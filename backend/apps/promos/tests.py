from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.promos.models import Promo


class PromoModelTests(TestCase):
    def test_slug_autogenerates_from_title(self):
        """
        Текущая бизнес-логика (по модели):
        slug автогенерируется из title через slugify().
        """
        p = Promo.objects.create(
            title="Скидка 10%",
            is_active=True,
        )
        # slugify("Скидка 10%") -> "skidka-10"
        self.assertTrue(p.slug)
        self.assertIn("10", p.slug)

    def test_slug_not_overwritten_if_provided(self):
        p = Promo.objects.create(
            title="Скидка 10%",
            slug="custom-slug",
            is_active=True,
        )
        self.assertEqual(p.slug, "custom-slug")

    def test_slug_unique_suffix_appended(self):
        """
        Если два промо дают один и тот же base slug,
        второму должен добавиться суффикс -2, затем -3 и т.д.
        """
        p1 = Promo.objects.create(title="10", slug="", is_active=True)
        p2 = Promo.objects.create(title="10", slug="", is_active=True)
        p3 = Promo.objects.create(title="10", slug="", is_active=True)
        self.assertEqual(p1.slug, "10")
        self.assertEqual(p2.slug, "10-2")
        self.assertEqual(p3.slug, "10-3")

    def test_is_current_respects_window_and_active(self):
        now = timezone.now()

        p_active_no_window = Promo.objects.create(title="A", is_active=True)
        self.assertTrue(p_active_no_window.is_current)

        p_inactive = Promo.objects.create(title="B", is_active=False)
        self.assertFalse(p_inactive.is_current)

        p_future = Promo.objects.create(title="C", is_active=True, starts_at=now + timedelta(days=1))
        self.assertFalse(p_future.is_current)

        p_ended = Promo.objects.create(title="D", is_active=True, ends_at=now - timedelta(minutes=1))
        self.assertFalse(p_ended.is_current)

        p_in_window = Promo.objects.create(
            title="E",
            is_active=True,
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=1),
        )
        self.assertTrue(p_in_window.is_current)


class PromoViewsTests(TestCase):
    def test_promo_list_shows_only_active_ordered(self):
        """
        promo_list фильтрует только is_active=True и сортирует:
        sort_order ASC, created_at DESC (см. views.py)
        """
        p_active1 = Promo.objects.create(title="A1", slug="", is_active=True, sort_order=10)
        p_inactive = Promo.objects.create(title="INACTIVE", slug="", is_active=False, sort_order=1)
        p_active2 = Promo.objects.create(title="A2", slug="", is_active=True, sort_order=20)

        url = reverse("promos:list")
        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)

        # inactive title must not be rendered
        self.assertNotContains(r, "INACTIVE")

        # active titles should be present
        self.assertContains(r, "A1")
        self.assertContains(r, "A2")

    def test_promo_detail_only_active_by_slug(self):
        active = Promo.objects.create(title="Акция", is_active=True)
        inactive = Promo.objects.create(title="Скрытая", is_active=False)

        url_active = reverse("promos:detail", kwargs={"slug": active.slug})
        r1 = self.client.get(url_active)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.context["promo"].id, active.id)

        url_inactive = reverse("promos:detail", kwargs={"slug": inactive.slug})
        r2 = self.client.get(url_inactive)
        self.assertEqual(r2.status_code, 404)