"""
Notification utilities for feedback processing.

This module contains:
- FeedbackNotification dataclass (transport object)
- Email notification sender
- Telegram notification sender

Used by core.views when processing feedback form submissions.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail


@dataclass
class FeedbackNotification:
    """
    Transport object for feedback data.

    Attributes:
        name: Sender name.
        contact: Phone or email provided by the user.
        message: Feedback message text.
        page_url: Absolute URL of the page where the form was submitted.
    """

    name: str
    contact: str
    message: str
    page_url: str = ""


def notify_feedback_email(payload: FeedbackNotification) -> None:
    """
    Send feedback notification via email.

    Email recipient is resolved in the following order:
        1. settings.FEEDBACK_TO_EMAIL
        2. settings.DEFAULT_FROM_EMAIL

    If no recipient is configured, function exits silently.

    Args:
        payload: FeedbackNotification object with form data.

    Returns:
        None
    """
    subject = f"Mediscan: обратная связь от {payload.name}"

    lines = [
        f"Имя: {payload.name}",
        f"Контакт: {payload.contact}",
        f"Страница: {payload.page_url}" if payload.page_url else "",
        "",
        "Сообщение:",
        payload.message,
    ]

    body = "\n".join([x for x in lines if x != ""])

    to_email = (
        getattr(settings, "FEEDBACK_TO_EMAIL", None)
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    )

    if not to_email:
        return

    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[to_email],
        fail_silently=True,
    )


def notify_feedback_telegram(payload: FeedbackNotification) -> None:
    """
    Send feedback notification to Telegram.

    Formats message using Markdown-style text and delegates
    actual sending to `notify_telegram_text` from appointments app.

    Args:
        payload: FeedbackNotification object with form data.

    Returns:
        None
    """
    text = (
        "📩 *Обратная связь*\n"
        f"*Имя:* {payload.name}\n"
        f"*Контакт:* {payload.contact}\n"
        f"*Страница:* {payload.page_url}\n\n"
        f"*Сообщение:*\n{payload.message}"
    )

    # Imported locally to avoid circular dependency
    from apps.appointments.notifications import notify_telegram_text  # noqa

    notify_telegram_text(text)