import pytest
from django.contrib.messages import get_messages
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from unittest.mock import Mock, patch

from apps.core.context_processors import core_context
from apps.core.forms import FeedbackForm
from apps.core.models import City, License, SiteSettings
from apps.core.notifications import FeedbackNotification, notify_feedback_email, notify_feedback_telegram


pytestmark = pytest.mark.django_db


# -----------------------
# Helpers
# -----------------------
def _add_session_to_request(request):
    """
    Attach a working session to a RequestFactory request.
    """
    from django.contrib.sessions.middleware import SessionMiddleware

    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    return request


# -----------------------
# Model tests
# -----------------------
def test_city_str():
    city = City.objects.create(name="Москва")
    assert str(city) == "Москва"


def test_sitesettings_str():
    settings_obj = SiteSettings.objects.create(site_name="Mediscan")
    assert str(settings_obj) == "Site settings"


def test_license_str():
    lic = License.objects.create(title="Лицензия 1", file="licenses/lic1.pdf")
    assert str(lic) == "Лицензия 1"


def test_license_ordering_by_sort_order_then_created_at_desc():
    """
    Ordering is: sort_order ASC, created_at DESC
    """
    # Same sort_order -> created_at should be DESC
    a = License.objects.create(title="A", file="licenses/a.pdf", sort_order=10)
    b = License.objects.create(title="B", file="licenses/b.pdf", sort_order=10)

    # Force created_at values to be different (update after create)
    License.objects.filter(pk=a.pk).update(created_at=timezone.now() - timezone.timedelta(days=1))
    License.objects.filter(pk=b.pk).update(created_at=timezone.now())

    a.refresh_from_db()
    b.refresh_from_db()

    # Different sort_order should come first
    c = License.objects.create(title="C", file="licenses/c.pdf", sort_order=1)

    qs = list(License.objects.all())
    assert qs[0].pk == c.pk  # sort_order=1 first

    # Among same sort_order=10, newest created_at should be first
    rest = [x for x in qs if x.sort_order == 10]
    assert rest[0].pk == b.pk
    assert rest[1].pk == a.pk


# -----------------------
# Form tests
# -----------------------
def test_feedback_form_widget_attrs_are_applied():
    form = FeedbackForm()

    assert "class" in form.fields["name"].widget.attrs
    assert form.fields["name"].widget.attrs["placeholder"] == "Например: Анна"

    assert "class" in form.fields["contact"].widget.attrs
    assert form.fields["contact"].widget.attrs["placeholder"] == "+7… или email@…"

    assert "class" in form.fields["message"].widget.attrs
    assert form.fields["message"].widget.attrs["rows"] == 4
    assert form.fields["message"].widget.attrs["placeholder"].startswith("Например:")


def test_feedback_form_valid_data():
    form = FeedbackForm(
        data={
            "name": "Анна",
            "contact": "anna@example.com",
            "message": "Хочу уточнить подготовку к УЗИ",
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["name"] == "Анна"


# -----------------------
# Context processor tests
# -----------------------
def test_core_context_returns_settings_cities_and_current_city():
    SiteSettings.objects.create(site_name="Mediscan")
    city1 = City.objects.create(name="Москва", is_active=True)
    City.objects.create(name="СПБ", is_active=False)

    rf = RequestFactory()
    request = rf.get("/")
    _add_session_to_request(request)
    request.session["city_id"] = city1.id
    request.session.save()

    ctx = core_context(request)

    assert "settings" in ctx
    assert ctx["settings"].site_name == "Mediscan"
    assert list(ctx["cities"]) == [city1]
    assert ctx["current_city"] == city1


# -----------------------
# Notifications tests
# -----------------------
def test_notify_feedback_email_sends_when_recipient_configured(settings):
    settings.DEFAULT_FROM_EMAIL = "no-reply@mediscan.local"
    settings.FEEDBACK_TO_EMAIL = "owner@mediscan.local"

    payload = FeedbackNotification(
        name="Анна",
        contact="+79990000000",
        message="Тест",
        page_url="https://example.com/contacts/",
    )

    with patch("apps.core.notifications.send_mail") as mocked:
        notify_feedback_email(payload)

    mocked.assert_called_once()
    args, kwargs = mocked.call_args
    assert "обратная связь" in kwargs["subject"].lower() or "обратная связь" in args[0].lower()
    assert "Анна" in (kwargs.get("message") or args[1])
    assert kwargs["recipient_list"] == ["owner@mediscan.local"]


def test_notify_feedback_email_returns_silently_when_no_recipient(settings):
    settings.DEFAULT_FROM_EMAIL = ""
    if hasattr(settings, "FEEDBACK_TO_EMAIL"):
        settings.FEEDBACK_TO_EMAIL = ""

    payload = FeedbackNotification(name="Анна", contact="x", message="y")

    with patch("apps.core.notifications.send_mail") as mocked:
        notify_feedback_email(payload)

    mocked.assert_not_called()


def test_notify_feedback_telegram_calls_appointments_sender(monkeypatch):
    payload = FeedbackNotification(
        name="Анна",
        contact="anna@example.com",
        message="Сообщение",
        page_url="https://example.com/contacts/",
    )

    fake_sender = Mock()
    monkeypatch.setattr("apps.appointments.notifications.notify_telegram_text", fake_sender)

    notify_feedback_telegram(payload)

    fake_sender.assert_called_once()
    sent_text = fake_sender.call_args[0][0]
    assert "Обратная связь" in sent_text
    assert payload.name in sent_text
    assert payload.contact in sent_text


# -----------------------
# View tests
# -----------------------
def test_home_view_renders_ok(client: Client):
    SiteSettings.objects.create(site_name="Mediscan")
    city = City.objects.create(name="Москва", is_active=True)

    # set city in session
    session = client.session
    session["city_id"] = city.id
    session.save()

    # home url может быть не в core/urls.py, поэтому вызываем напрямую, если в проекте есть маршрут.
    # Если home подключен иначе — просто поменяй reverse на свой url-name.
    # Попробуем сначала "home", если его нет — пропустим.
    try:
        url = reverse("home")
    except Exception:
        pytest.skip("No global url named 'home' found in project urls.")

    resp = client.get(url)
    assert resp.status_code == 200
    assert "settings" in resp.context
    assert "cities" in resp.context
    assert "current_city" in resp.context


def test_contacts_get_renders_form(client: Client):
    SiteSettings.objects.create(site_name="Mediscan")
    City.objects.create(name="Москва", is_active=True)

    url = reverse("core:contacts")
    resp = client.get(url)

    assert resp.status_code == 200
    assert "form" in resp.context
    assert isinstance(resp.context["form"], FeedbackForm)


def test_contacts_post_valid_sends_notifications_and_redirects(client: Client):
    """
    POST valid -> notify email + telegram + success message + redirect (PRG)
    """
    SiteSettings.objects.create(site_name="Mediscan")
    City.objects.create(name="Москва", is_active=True)

    url = reverse("core:contacts")

    # Важно: views.contacts использует reverse("contacts") без namespace.
    # Чтобы тест не зависел от project urls, патчим reverse внутри apps.core.views
    with patch("apps.core.views.reverse", return_value="/contacts/"), patch(
        "apps.core.views.notify_feedback_email"
    ) as email_mock, patch(
        "apps.core.views.notify_feedback_telegram"
    ) as tg_mock:
        resp = client.post(
            url,
            data={
                "name": "Анна",
                "contact": "anna@example.com",
                "message": "Тест",
            },
        )

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(url)

    email_mock.assert_called_once()
    tg_mock.assert_called_once()

    # Проверим, что записалось success message
    follow = client.get(url)
    msgs = [m.message for m in get_messages(follow.wsgi_request)]
    assert any("Спасибо" in m for m in msgs)


def test_contacts_post_invalid_shows_error_message(client: Client):
    SiteSettings.objects.create(site_name="Mediscan")
    City.objects.create(name="Москва", is_active=True)

    url = reverse("core:contacts")

    resp = client.post(url, data={"name": "", "contact": "", "message": ""})
    assert resp.status_code == 200  # не редиректит, рендерит форму с ошибками

    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("Проверьте форму" in m for m in msgs)


def test_set_city_sets_session_and_redirects_back(client: Client):
    city = City.objects.create(name="Москва", is_active=True)
    url = reverse("core:set_city", kwargs={"city_id": city.id})

    resp = client.get(url, HTTP_REFERER="/contacts/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/contacts/"

    session = client.session
    assert session.get("city_id") == city.id


def test_set_city_404_for_inactive_city(client: Client):
    city = City.objects.create(name="СПБ", is_active=False)
    url = reverse("core:set_city", kwargs={"city_id": city.id})

    resp = client.get(url)
    assert resp.status_code == 404