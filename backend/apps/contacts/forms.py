"""
Forms for contacts application.

Includes:
- ContactForm: name + email + message
- AskQuestionForm: name + contact + question
"""

from __future__ import annotations

from django import forms


class ContactForm(forms.Form):
    """
    Generic contact form used on Contacts and Feedback pages.
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
        """Validate name length and strip whitespace."""
        v = (self.cleaned_data.get("name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Введите имя (минимум 2 символа).")
        return v


class AskQuestionForm(forms.Form):
    """
    Form for asking a question (name + contact + question).
    """

    name = forms.CharField(label="Ваше имя", max_length=120, required=True)
    contact = forms.CharField(label="Телефон или Email", max_length=120, required=True)
    question = forms.CharField(
        label="Вопрос",
        required=True,
        widget=forms.Textarea(attrs={"rows": 6}),
    )

    def clean_name(self) -> str:
        """Validate name length and strip whitespace."""
        v = (self.cleaned_data.get("name") or "").strip()
        if len(v) < 2:
            raise forms.ValidationError("Введите имя (минимум 2 символа).")
        return v

    def clean_contact(self) -> str:
        """Validate contact length and strip whitespace."""
        v = (self.cleaned_data.get("contact") or "").strip()
        if len(v) < 5:
            raise forms.ValidationError("Укажите телефон или email.")
        return v

    def clean_question(self) -> str:
        """Validate question length and strip whitespace."""
        v = (self.cleaned_data.get("question") or "").strip()
        if len(v) < 5:
            raise forms.ValidationError("Опишите вопрос (минимум 5 символов).")
        return v