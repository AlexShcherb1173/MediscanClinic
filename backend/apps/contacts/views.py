from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import ContactForm
from .notifications import notify_contact_email, notify_contact_telegram


def contacts_home(request):
    base_ctx = {
        "address": "г. Москва, Бережковская набережная, д. 16А5, стр. 3",
        "phone_display": "+7(985)698-72-82",
        "phone_tel": "+79856987282",
        "email": "lenovo2015549@gmail.com",
        "map_query": "г. Москва, Бережковская набережная, д. 16А5, стр. 3",
    }

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message_text = form.cleaned_data["message"]

            subject = f"Mediscan: сообщение с сайта (Контакты) от {name}"
            text = (
                f"Новое сообщение с формы Контакты\n\n"
                f"Имя: {name}\n"
                f"Email: {email}\n\n"
                f"Сообщение:\n{message_text}\n"
            )

            # Email + Telegram админу
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

    # GET
    return render(request, "contacts/home.html", {**base_ctx, "form": ContactForm()})