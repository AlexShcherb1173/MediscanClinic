from dataclasses import dataclass
from django.conf import settings
from django.core.mail import send_mail


@dataclass
class FeedbackNotification:
    name: str
    contact: str
    message: str
    page_url: str = ""


def notify_feedback_email(payload: FeedbackNotification) -> None:
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

    to_email = getattr(settings, "FEEDBACK_TO_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
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
    text = (
        "📩 *Обратная связь*\n"
        f"*Имя:* {payload.name}\n"
        f"*Контакт:* {payload.contact}\n"
        f"*Страница:* {payload.page_url}\n\n"
        f"*Сообщение:*\n{payload.message}"
    )

    from apps.appointments.notifications import notify_telegram_text  # noqa
    notify_telegram_text(text)