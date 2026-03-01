from __future__ import annotations

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from apps.notifications.tasks import send_telegram_text_task
from apps.notifications.telegram_client import send_telegram_message


class TelegramClientTests(TestCase):
    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    def test_send_telegram_message_no_config_returns_false(self):
        ok = send_telegram_message("hello")
        self.assertFalse(ok)

    @override_settings(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_CHAT_ID="123",
        TELEGRAM_API_BASE="https://api.telegram.org",
    )
    @patch("apps.notifications.telegram_client.requests.post")
    def test_send_telegram_message_success(self, post):
        post.return_value = Mock(ok=True, status_code=200, text="ok")
        ok = send_telegram_message("hello")
        self.assertTrue(ok)
        post.assert_called_once()

    @override_settings(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_CHAT_ID="123",
        TELEGRAM_API_BASE="https://api.telegram.org",
    )
    @patch("apps.notifications.telegram_client.requests.post")
    def test_send_telegram_message_http_error_returns_false(self, post):
        post.return_value = Mock(ok=False, status_code=400, text="bad request")
        ok = send_telegram_message("hello")
        self.assertFalse(ok)

    @override_settings(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_CHAT_ID="123",
        TELEGRAM_API_BASE="https://api.telegram.org",
    )
    @patch("apps.notifications.telegram_client.requests.post")
    def test_send_telegram_message_exception_returns_false(self, post):
        post.side_effect = RuntimeError("network down")
        ok = send_telegram_message("hello")
        self.assertFalse(ok)

    @override_settings(
        TELEGRAM_BOT_TOKEN="token",
        TELEGRAM_CHAT_ID="123",
        TELEGRAM_API_BASE="https://api.telegram.org",
    )
    @patch("apps.notifications.telegram_client.requests.post")
    def test_send_telegram_message_truncates_long_text(self, post):
        post.return_value = Mock(ok=True, status_code=200, text="ok")
        long_text = "x" * 5000
        ok = send_telegram_message(long_text)
        self.assertTrue(ok)

        # verify request payload text length is not > 4096
        args, kwargs = post.call_args
        payload = kwargs["json"]
        self.assertLessEqual(len(payload["text"]), 4096)


class NotificationsTasksTests(TestCase):
    @patch("apps.notifications.tasks.send_telegram_message")
    def test_send_telegram_text_task_raises_on_failure(self, send):
        send.return_value = False
        with self.assertRaises(RuntimeError):
            send_telegram_text_task.run("hi")

    @patch("apps.notifications.tasks.send_telegram_message")
    def test_send_telegram_text_task_ok(self, send):
        send.return_value = True
        # should not raise
        send_telegram_text_task.run("hi")
