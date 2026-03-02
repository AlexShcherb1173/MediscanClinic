"""
Формы приложения контактов (contacts).
Содержит:
- ContactForm — универсальная форма обратной связи (имя + email + сообщение);
- AskQuestionForm — форма вопроса (имя + контакт + текст вопроса).
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.contact_utils import normalize_phone_or_email


class ContactForm(forms.Form):
    """
    Универсальная форма обратной связи.
    Используется на страницах «Контакты» и «Обратная связь».
    Содержит поля:
        - name — имя пользователя;
        - email — email для ответа;
        - message — текст сообщения.
    """

    name = forms.CharField(
        label="Ваше имя",
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Ваше имя"}),
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    message = forms.CharField(
        label="Сообщение",
        required=True,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Сообщение"}),
    )

    def clean_name(self) -> str:
        """
        Валидирует имя пользователя.
        Логика:
            - удаляет лишние пробелы по краям;
            - проверяет минимальную длину (не менее 2 символов).
        Возвращает:
            str: Очищенное имя.
        Вызывает:
            ValidationError: если имя слишком короткое.
        """
        v = (self.cleaned_data.get("name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Введите имя (минимум 2 символа).")
        return v

class AskQuestionForm(forms.Form):
    """
    Форма для отправки вопроса.
    Содержит:
        - name — имя пользователя;
        - contact — телефон или email для обратной связи;
        - question — текст вопроса.
    """

    name = forms.CharField(label="Ваше имя", max_length=120, required=True)
    contact = forms.CharField(label="Телефон или Email", max_length=120, required=True)
    question = forms.CharField(
        label="Вопрос",
        required=True,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    def clean_name(self) -> str:
        """
        Валидирует имя пользователя.
        Логика:
            - удаляет лишние пробелы;
            - проверяет минимальную длину (не менее 2 символов).
        """
        v = (self.cleaned_data.get("name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Введите имя (минимум 2 символа).")
        return v

    def clean_contact(self):
        """
        Валидирует и нормализует контактные данные.
        Принимает телефон или email.
        Использует normalize_phone_or_email() для определения типа
        и приведения к стандартному виду:
            - email → в нижнем регистре;
            - телефон → формат E.164.
        Возвращает:
            str: Нормализованное значение контакта.
        Вызывает:
            ValidationError: если введённые данные не являются
            корректным телефоном или email.
        """
        raw = self.cleaned_data.get("contact", "")
        try:
            normalized = normalize_phone_or_email(raw)
        except ValidationError as e:
            raise forms.ValidationError("Укажите телефон или email")

        # Вернём нормализованную строку (email lower / телефон E.164)
        return normalized.value

    def clean_question(self) -> str:
        """
        Валидирует текст вопроса.
        Логика:
            - удаляет лишние пробелы;
            - проверяет минимальную длину (не менее 5 символов).
        Возвращает:
            str: Очищенный текст вопроса.
        Вызывает:
            ValidationError: если текст слишком короткий.
        """
        v = (self.cleaned_data.get("question") or "").strip()
        if len(v) < 5:
            raise forms.ValidationError("Опишите вопрос (минимум 5 символов).")
        return v
