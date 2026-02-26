from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.promos.models import Promo
from apps.services.models import Service, ServiceCategory


class PromosBaseMixin:
    def create_category(self, name="Категория", is_active=True):
        return ServiceCategory.objects.create(
            name=name,
            slug=name.lower().replace(" ", "-"),
            order=0,
            is_active=is_active,
        )

    def create_service(self, category=None, name="Услуга", is_active=True, price_from="1000.00"):
        category = category or self.create_category()
        return Service.objects.create(
            category=category,
            name=name,
            slug=name.lower().replace(" ", "-"),
            description="",
            price_from=price_from,
            price_to=None,
            is_active=is_active,
            is_featured=False,
            featured_order=0,
        )


class PromoModelTests(PromosBaseMixin, TestCase):
    def test_str(self):
        p = Promo.objects.create(title="Скидка 10%")
        self.assertEqual(str(p), "Скидка 10%")

    def test_slug_autogenerates(self):
        p = Promo.objects.create(title="Скидка 10% на МРТ", slug="")
        self.assertTrue(p.slug)
        self.assertIn("skidka", p.slug)  # slugify -> latin

    def test_slug_unique_suffix(self):
        p1 = Promo.objects.create(title="Одна акция", slug="")
        p2 = Promo.objects.create(title="Одна акция", slug="")
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.startswith(p1.slug + "-") or p2.slug != p1.slug)

    def test_is_current_inactive(self):
        p = Promo.objects.create(title="X", is_active=False)
        self.assertFalse(p.is_current)

    def test_is_current_with_starts_at_future(self):
        p = Promo.objects.create(
            title="X",
            is_active=True,
            starts_at=timezone.now() + timedelta(hours=1),
        )
        self.assertFalse(p.is_current)

    def test_is_current_with_ends_at_past(self):
        p = Promo.objects.create(
            title="X",
            is_active=True,
            ends_at=timezone.now() - timedelta(hours=1),
        )
        self.assertFalse(p.is_current)

    def test_is_current_ok_when_in_window(self):
        p = Promo.objects.create(
            title="X",
            is_active=True,
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        self.assertTrue(p.is_current)


class PromoViewsTests(PromosBaseMixin, TestCase):
    def test_promo_list_shows_only_active(self):
        Promo.objects.create(title="A1", is_active=True, sort_order=10)
        Promo.objects.create(title="A2", is_active=False, sort_order=0)

        url = reverse("promos:list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "A1")
        self.assertNotContains(r, "A2")

    def test_promo_detail_404_for_inactive(self):
        p = Promo.objects.create(title="Hidden", is_active=False, slug="hidden")
        url = reverse("promos:detail", kwargs={"slug": p.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_promo_detail_filters_services_by_active_and_category_active(self):
        cat_active = self.create_category("Активная", is_active=True)
        cat_inactive = self.create_category("Неактивная", is_active=False)

        s_ok = self.create_service(category=cat_active, name="OK", is_active=True)
        s_inactive = self.create_service(category=cat_active, name="S_INACTIVE", is_active=False)
        s_bad_cat = self.create_service(category=cat_inactive, name="BAD_CAT", is_active=True)

        promo = Promo.objects.create(title="Promo", is_active=True, slug="promo")
        promo.services.add(s_ok, s_inactive, s_bad_cat)

        url = reverse("promos:detail", kwargs={"slug": promo.slug})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        promo_services = r.context["promo_services"]
        self.assertEqual(list(promo_services), [s_ok])