"""
Представления приложения контактов (contacts).
Страницы:
- contacts_home — страница «Контакты» (карта + форма сообщения);
- feedback_home — страница «Обратная связь» (форма сообщения);
- ask_question — страница «Задать вопрос».
Обработчики POST-запросов:
- валидируют форму;
- отправляют уведомления администратору (Email + Telegram);
- показывают сообщение об успехе и делают редирект на эту же страницу.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import AskQuestionForm, ContactForm
from .notifications import notify_contact_email, notify_contact_telegram


def _send_feedback(form: ContactForm) -> None:
    """
    Отправляет сообщение из формы обратной связи (Email + Telegram).
    Ожидается, что форма уже провалидирована (form.is_valid() == True).
    Параметры:
        form (ContactForm): Валидированная форма ContactForm.
    Побочные эффекты:
        - отправляет email администратору через notify_contact_email();
        - отправляет сообщение в Telegram через notify_contact_telegram().
    """
    name = form.cleaned_data["name"]
    email = form.cleaned_data["email"]
    message_text = form.cleaned_data["message"]

    subject = f"Mediscan: сообщение с сайта (Обратная связь) от {name}"
    text = (
        "Новое сообщение с формы Обратной связи\n\n"
        f"Имя: {name}\n"
        f"Email: {email}\n\n"
        f"Сообщение:\n{message_text}\n"
    )
    notify_contact_email(subject, text)

    tg_text = (
        "<b>Mediscan — Обратная связь</b>\n"
        "<b>Новое сообщение</b>\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Email:</b> {email}\n\n"
        f"<b>Текст:</b>\n{message_text}"
    )
    notify_contact_telegram(tg_text)


def contacts_home(request):
    """
    Страница «Контакты» с картой и формой сообщения.
    GET:
        - отображает страницу и пустую форму ContactForm;
        - передаёт в контекст адрес/контакты и ключ Yandex Maps.
    POST:
        - валидирует ContactForm;
        - при успехе отправляет уведомления администратору (Email + Telegram),
          показывает success-message и делает редирект на contacts:home;
        - при ошибках валидации повторно рендерит страницу с ошибками формы.
    """
    address = "г. Москва, Бережковская набережная, д. 16А5, стр. 5"
    base_ctx = {
        "address": address,
        "phone_display": "+7(985)698-72-82",
        "phone_tel": "+79856987282",
        "email": "lenovo2015549@gmail.com",
        "telegram_username": "@ALEX_181173",
        "map_query": address,
        "ymaps_api_key": getattr(settings, "YMAPS_API_KEY", ""),
    }

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message_text = form.cleaned_data["message"]

            subject = f"Mediscan: сообщение с сайта (Контакты) от {name}"
            text = (
                "Новое сообщение с формы Контакты\n\n"
                f"Имя: {name}\n"
                f"Email: {email}\n\n"
                f"Сообщение:\n{message_text}\n"
            )

            notify_contact_email(subject, text)

            tg_text = (
                "<b>Mediscan — Контакты</b>\n"
                "<b>Новое сообщение</b>\n\n"
                f"<b>Имя:</b> {name}\n"
                f"<b>Email:</b> {email}\n\n"
                f"<b>Текст:</b>\n{message_text}"
            )
            notify_contact_telegram(tg_text)

            messages.success(request, "Сообщение отправлено! Мы скоро свяжемся с вами.")
            return redirect(reverse("contacts:home"))

        return render(request, "contacts/home.html", {**base_ctx, "form": form})

    return render(request, "contacts/home.html", {**base_ctx, "form": ContactForm()})


def feedback_home(request):
    """
    Страница «Обратная связь» (упрощённая форма контактов).
    GET:
        - отображает страницу и пустую форму ContactForm.
    POST:
        - валидирует ContactForm;
        - при успехе отправляет уведомления через helper _send_feedback(),
          показывает success-message и делает редирект на contacts:feedback;
        - при ошибках валидации повторно рендерит страницу с ошибками формы.
    """
    base_ctx = {
        "phone_display": "+7(985)698-72-82",
        "phone_tel": "+79856987282",
        "email": "lenovo2015549@gmail.com",
        "telegram_username": "@ALEX_181173",
    }

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            _send_feedback(form)
            messages.success(request, "Сообщение отправлено! Мы скоро свяжемся с вами.")
            return redirect(reverse("contacts:feedback"))
        return render(request, "contacts/feedback.html", {**base_ctx, "form": form})

    return render(request, "contacts/feedback.html", {**base_ctx, "form": ContactForm()})


def ask_question(request):
    """
    Страница «Задать вопрос».
    GET:
        - отображает страницу и пустую форму AskQuestionForm.
    POST:
        - валидирует AskQuestionForm;
        - при успехе отправляет уведомления администратору (Email + Telegram),
          показывает success-message и делает редирект на contacts:ask_question;
        - при ошибках валидации повторно рендерит страницу с ошибками формы.
    """
    base_ctx = {
        "phone_display": "+7(985)698-72-82",
        "phone_tel": "+79856987282",
        "email": "lenovo2015549@gmail.com",
        "telegram_username": "@ALEX_181173",
    }

    if request.method == "POST":
        form = AskQuestionForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            contact = form.cleaned_data["contact"]
            question = form.cleaned_data["question"]

            subject = f"Mediscan: вопрос с сайта от {name}"
            text = "Новый вопрос с сайта\n\n" f"Имя: {name}\n" f"Контакт: {contact}\n\n" f"Вопрос:\n{question}\n"
            notify_contact_email(subject, text)

            tg_text = (
                "<b>Mediscan — Вопрос с сайта</b>\n"
                "<b>Новый вопрос</b>\n\n"
                f"<b>Имя:</b> {name}\n"
                f"<b>Контакт:</b> {contact}\n\n"
                f"<b>Вопрос:</b>\n{question}"
            )
            notify_contact_telegram(tg_text)

            messages.success(request, "Вопрос отправлен! Мы скоро ответим.")
            return redirect(reverse("contacts:ask_question"))

        return render(request, "contacts/ask_question.html", {**base_ctx, "form": form})

    return render(request, "contacts/ask_question.html", {**base_ctx, "form": AskQuestionForm()})
