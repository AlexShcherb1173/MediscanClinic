from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.contacts.forms import AskQuestionForm, ContactForm
from apps.contacts.notifications import notify_contact_telegram
from apps.contacts.telegram import send_telegram_message


class ContactsFormsTests(TestCase):
    def test_contact_form_clean_name(self):
        f = ContactForm(data={"name": " A ", "email": "a@a.com", "message": "Hello"})
        self.assertFalse(f.is_valid())
        self.assertIn("name", f.errors)

        f2 = ContactForm(data={"name": "Анна", "email": "a@a.com", "message": "Hello"})
        self.assertTrue(f2.is_valid())
        self.assertEqual(f2.cleaned_data["name"], "Анна")

    def test_ask_question_form_validation(self):
        f = AskQuestionForm(data={"name": "A", "contact": "1", "question": "x"})
        self.assertFalse(f.is_valid())
        self.assertIn("name", f.errors)
        self.assertIn("contact", f.errors)
        self.assertIn("question", f.errors)

        f2 = AskQuestionForm(data={"name": "Alex", "contact": "test@test.com", "question": "Hello?"})
        self.assertTrue(f2.is_valid())


class ContactsViewsTests(TestCase):
    @patch("apps.contacts.views.notify_contact_email")
    @patch("apps.contacts.views.notify_contact_telegram")
    def test_contacts_home_post_valid_sends_notifications_and_redirects(self, tg, em):
        url = reverse("contacts:home")
        r = self.client.post(url, data={"name": "Alex", "email": "a@a.com", "message": "Hi"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], url)

        em.assert_called_once()
        tg.assert_called_once()

    @patch("apps.contacts.views.notify_contact_email")
    @patch("apps.contacts.views.notify_contact_telegram")
    def test_feedback_post_valid_sends_notifications_and_redirects(self, tg, em):
        url = reverse("contacts:feedback")
        r = self.client.post(url, data={"name": "Alex", "email": "a@a.com", "message": "Hi"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], url)

        em.assert_called_once()
        tg.assert_called_once()

    @patch("apps.contacts.views.notify_contact_email")
    @patch("apps.contacts.views.notify_contact_telegram")
    def test_ask_question_post_valid_sends_notifications_and_redirects(self, tg, em):
        url = reverse("contacts:ask_question")
        r = self.client.post(url, data={"name": "Alex", "contact": "+7999", "question": "How?"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], url)

        em.assert_called_once()
        tg.assert_called_once()

    def test_contacts_pages_get_ok(self):
        r1 = self.client.get(reverse("contacts:home"))
        r2 = self.client.get(reverse("contacts:feedback"))
        r3 = self.client.get(reverse("contacts:ask_question"))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r3.status_code, 200)


class ContactsNotificationsTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_ADMIN_CHAT_ID="")
    def test_notify_contact_telegram_no_settings_is_noop(self):
        # should not raise
        notify_contact_telegram("<b>test</b>")

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_ADMIN_CHAT_ID="", TELEGRAM_API_URL="")
    def test_admin_telegram_client_requires_settings(self):
        with self.assertRaises(RuntimeError):
            send_telegram_message("hello")