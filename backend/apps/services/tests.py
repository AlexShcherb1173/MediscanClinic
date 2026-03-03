from __future__ import annotations

from decimal import Decimal
from urllib.parse import parse_qs, unquote, urlparse

from apps.services.context_processors import popular_services
from apps.services.models import Service, ServiceCategory
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse


class ServiceModelsTests(TestCase):
    def test_service_category_str_and_slug_autofill(self):
        cat = ServiceCategory.objects.create(name="УЗИ", slug="")
        self.assertEqual(str(cat), "УЗИ")
        self.assertTrue(cat.slug)
        self.assertNotIn(" ", cat.slug)

    def test_service_str_and_slug_autofill(self):
        cat = ServiceCategory.objects.create(name="УЗИ", slug="uzi")
        svc = Service.objects.create(
            category=cat,
            name="УЗИ брюшной полости",
            slug="",
            price_from=Decimal("100.00"),
        )
        self.assertEqual(str(svc), "УЗИ брюшной полости")
        self.assertTrue(svc.slug)

    def test_service_clean_rejects_price_to_less_than_price_from(self):
        cat = ServiceCategory.objects.create(name="Анализы", slug="analizy")
        svc = Service(
            category=cat,
            name="Анализ крови",
            slug="analiz-krovi",
            price_from=Decimal("500.00"),
            price_to=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError) as exc:
            svc.clean()
        self.assertIn("price_to", exc.exception.message_dict)


class ServicesContextProcessorTests(TestCase):
    def test_popular_services_context_returns_featured_sorted_and_limited(self):
        cat = ServiceCategory.objects.create(name="УЗИ", slug="uzi", is_active=True)

        # Create 5 featured -> should return only first 4
        Service.objects.create(
            category=cat,
            name="B",
            slug="b",
            price_from=Decimal("100.00"),
            is_active=True,
            is_featured=True,
            featured_order=2,
        )
        Service.objects.create(
            category=cat,
            name="A",
            slug="a",
            price_from=Decimal("100.00"),
            is_active=True,
            is_featured=True,
            featured_order=2,
        )
        Service.objects.create(
            category=cat,
            name="C",
            slug="c",
            price_from=Decimal("100.00"),
            is_active=True,
            is_featured=True,
            featured_order=1,
        )
        Service.objects.create(
            category=cat,
            name="D",
            slug="d",
            price_from=Decimal("100.00"),
            is_active=True,
            is_featured=True,
            featured_order=3,
        )
        Service.objects.create(
            category=cat,
            name="E",
            slug="e",
            price_from=Decimal("100.00"),
            is_active=True,
            is_featured=True,
            featured_order=4,
        )

        rf = RequestFactory()
        request = rf.get("/")
        ctx = popular_services(request)

        qs = list(ctx["popular_services"])
        self.assertEqual(len(qs), 4)
        self.assertEqual(qs[0].slug, "c")  # featured_order=1 -> C


def _create_services_dataset():
    active_cat = ServiceCategory.objects.create(name="УЗИ", slug="uzi", is_active=True)
    inactive_cat = ServiceCategory.objects.create(name="Скрытая", slug="hidden", is_active=False)

    # Active services in active category
    s1 = Service.objects.create(
        category=active_cat,
        name="УЗИ сердца",
        slug="uzi-serdca",
        price_from=Decimal("100.00"),
        is_active=True,
        is_featured=True,
        featured_order=1,
    )
    s2 = Service.objects.create(
        category=active_cat,
        name="УЗИ сосудов",
        slug="uzi-sosudov",
        price_from=Decimal("200.00"),
        is_active=True,
        is_featured=False,
    )
    s3 = Service.objects.create(
        category=active_cat,
        name="УЗИ печени",
        slug="uzi-pecheni",
        price_from=Decimal("300.00"),
        is_active=True,
        is_featured=False,
    )

    # Inactive service (should not appear)
    Service.objects.create(
        category=active_cat,
        name="Неактивная",
        slug="inactive",
        price_from=Decimal("150.00"),
        is_active=False,
    )

    # Service in inactive category (should not appear)
    Service.objects.create(
        category=inactive_cat,
        name="Категория скрыта",
        slug="hidden-cat",
        price_from=Decimal("150.00"),
        is_active=True,
    )

    return active_cat, s1, s2, s3


class ServicesViewsTests(TestCase):
    def test_service_list_view_basic(self):
        _create_services_dataset()

        url = reverse("services:list")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        services = list(resp.context["services"])
        self.assertTrue(all(s.is_active for s in services))

        slugs = {s.slug for s in services}
        self.assertNotIn("inactive", slugs)
        self.assertNotIn("hidden-cat", slugs)

    def test_service_list_view_saves_return_url_in_session(self):
        _create_services_dataset()

        url = reverse("services:list") + "?q=узи&sort=-price"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        saved = self.client.session.get("services_return_url")
        self.assertTrue(saved)
        self.assertTrue(saved.startswith("/services/?"))

        # sort должен сохраниться как есть
        self.assertIn("sort=-price", saved)

        # q должен декодироваться обратно в "узи", даже если у тебя “двойной” энкодинг
        parsed = urlparse(saved)
        qs = parse_qs(parsed.query)

        q_raw = (qs.get("q") or [""])[0]

        # 1) обычный percent-decode
        q1 = unquote(q_raw)

        # 2) если где-то случился “double-encoding” с промежуточным latin1 -> utf8,
        #    пробуем восстановить
        q2 = q1
        try:
            q2 = q1.encode("latin1").decode("utf-8")
        except Exception:
            pass

        self.assertIn("узи", {q1, q2})

    def test_service_list_view_filter_by_category(self):
        cat, *_ = _create_services_dataset()

        url = reverse("services:category", kwargs={"category_slug": cat.slug})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        services = list(resp.context["services"])
        self.assertTrue(all(s.category_id == cat.id for s in services))

    def test_service_list_view_search_q(self):
        _create_services_dataset()

        url = reverse("services:list") + "?q=печени"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        slugs = [s.slug for s in resp.context["services"]]
        self.assertEqual(slugs, ["uzi-pecheni"])

    def test_service_list_view_price_range_filters(self):
        _create_services_dataset()

        url = reverse("services:list") + "?price_min=150&price_max=250"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        slugs = [s.slug for s in resp.context["services"]]
        self.assertEqual(slugs, ["uzi-sosudov"])

    def test_service_list_view_sorting_by_price_desc(self):
        _create_services_dataset()

        url = reverse("services:list") + "?sort=-price"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        slugs = [s.slug for s in resp.context["services"]]
        self.assertEqual(slugs, ["uzi-pecheni", "uzi-sosudov", "uzi-serdca"])

    def test_service_detail_view_ok_for_active_service(self):
        _, s1, *_ = _create_services_dataset()

        url = reverse("services:detail", kwargs={"slug": s1.slug})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["service"].slug, s1.slug)
        self.assertIn("categories", resp.context)

    def test_service_detail_view_404_for_inactive_service(self):
        cat = ServiceCategory.objects.create(name="УЗИ", slug="uzi", is_active=True)
        Service.objects.create(
            category=cat,
            name="Неактивная",
            slug="inactive",
            price_from=Decimal("100.00"),
            is_active=False,
        )

        url = reverse("services:detail", kwargs={"slug": "inactive"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_service_detail_view_404_for_inactive_category(self):
        cat = ServiceCategory.objects.create(name="Скрытая", slug="hidden", is_active=False)
        Service.objects.create(
            category=cat,
            name="Услуга",
            slug="svc",
            price_from=Decimal("100.00"),
            is_active=True,
        )

        url = reverse("services:detail", kwargs={"slug": "svc"})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)
