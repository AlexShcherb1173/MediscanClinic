import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.pages.models import Page

pytestmark = pytest.mark.django_db


# -----------------------------------------------------------------------------
# Model tests
# -----------------------------------------------------------------------------
def test_page_str():
    page = Page.objects.create(title="О клинике", slug="about", content="x")
    assert str(page) == "О клинике"


def test_page_save_autogenerates_slug_when_empty():
    page = Page(title="Политика конфиденциальности", slug="")
    page.save()

    assert page.slug  # generated
    assert " " not in page.slug


# -----------------------------------------------------------------------------
# Management command tests
# -----------------------------------------------------------------------------
def test_seed_pages_command_creates_pages():
    call_command("seed_pages")

    assert Page.objects.filter(slug="about-history").exists()
    assert Page.objects.filter(slug="about-mission").exists()
    assert Page.objects.filter(slug="about-quality").exists()
    assert Page.objects.filter(slug="about-licenses").exists()


def test_seed_pages_command_is_idempotent():
    call_command("seed_pages")
    count1 = Page.objects.count()

    call_command("seed_pages")
    count2 = Page.objects.count()

    assert count1 == count2


# -----------------------------------------------------------------------------
# Views tests
# -----------------------------------------------------------------------------
def test_pages_home_renders_ok(client, monkeypatch):
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

    monkeypatch.setattr("apps.pages.views.Promo.objects.filter", lambda *a, **k: _PromoQS())

    # Service.objects.filter(...).select_related(...).order_by(... )[:4] -> []
    class _ServiceQS:
        def select_related(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def __getitem__(self, item):
            return []

    monkeypatch.setattr("apps.pages.views.Service.objects.filter", lambda *a, **k: _ServiceQS())

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

    monkeypatch.setattr("apps.pages.views.Doctor.objects.exclude", lambda *a, **k: _DoctorQS())

    url = reverse("pages:home")
    resp = client.get(url)

    assert resp.status_code == 200
    assert "promos" in resp.context
    assert "popular_services" in resp.context
    assert "doctors_slider" in resp.context


def test_pages_sitemap_renders_ok(client):
    url = reverse("pages:sitemap")
    resp = client.get(url)
    assert resp.status_code == 200


def test_page_detail_about_branch_renders_and_has_context(client, monkeypatch):
    """
    slug=about should render custom about template with doctors and licenses in context.
    We mock Doctor/License querysets to avoid DB dependencies and required fields.
    """

    class _DoctorFilterQS:
        def prefetch_related(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def __getitem__(self, item):
            return []

    monkeypatch.setattr(
        "apps.pages.views.Doctor.objects.filter",
        lambda *a, **k: _DoctorFilterQS(),
    )

    class _LicenseQS:
        def order_by(self, *args, **kwargs):
            return self

        def __getitem__(self, item):
            return []

    monkeypatch.setattr(
        "apps.pages.views.License.objects.filter",
        lambda *a, **k: _LicenseQS(),
    )

    url = reverse("pages:page_detail", kwargs={"slug": "about"})
    resp = client.get(url)

    assert resp.status_code == 200
    assert "doctors" in resp.context
    assert "licenses" in resp.context


def test_page_detail_static_template_slug_renders_ok(client):
    """
    Slug from STATIC_TEMPLATES should render without DB Page record.
    """
    url = reverse("pages:page_detail", kwargs={"slug": "privacy"})
    resp = client.get(url)
    assert resp.status_code == 200


def test_page_detail_db_page_published_renders_ok(client):
    Page.objects.create(title="FAQ", slug="faq", content="Hello", is_published=True)

    url = reverse("pages:page_detail", kwargs={"slug": "faq"})
    resp = client.get(url)

    assert resp.status_code == 200
    assert "page" in resp.context
    assert resp.context["page"].slug == "faq"


def test_page_detail_db_page_unpublished_returns_404(client):
    Page.objects.create(title="Hidden", slug="hidden", content="x", is_published=False)

    url = reverse("pages:page_detail", kwargs={"slug": "hidden"})
    resp = client.get(url)

    assert resp.status_code == 404