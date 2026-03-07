"""
Формы для приложения accounts.
Содержит:
- RegisterForm — регистрация по номеру телефона с подтверждением пароля
- LoginForm — аутентификация по номеру телефона через кастомный backend
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import EmailValidator, RegexValidator

from .utils import normalize_phone

User = get_user_model()

phone_validator = RegexValidator(
    regex=r"^\+?\d[\d\s\-\(\)]{8,20}$",
    message="Введите телефон в формате +79990000000 (можно пробелы/скобки/дефисы).",
)


class RegisterForm(forms.Form):
    """ "
    Форма регистрации пользователя (телефон + пароль + ФИО).
    Проверки:
        - номер телефона нормализуется и должен быть уникальным
        - пароль и подтверждение пароля должны совпадать
    """

    full_name = forms.CharField(label="ФИО", min_length=2, max_length=255)
    phone = forms.CharField(label="Телефон", max_length=24, validators=[phone_validator])
    email = forms.EmailField(label="Email", required=False, validators=[EmailValidator()])
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput, min_length=6)

    def clean_phone(self) -> str:
        """
        Нормализует номер телефона и проверяет его уникальность.
        """
        phone = normalize_phone(self.cleaned_data["phone"])
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует.")
        return phone

    def clean(self):
        """
        Проверяет совпадение пароля и подтверждения.
        """
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned

    if TYPE_CHECKING:
        from apps.accounts.models import User

    def save(self) -> "User":
        """
        Создаёт пользователя через UserManager.
        Возвращает:
        Созданный объект User.
        """
        return User.objects.create_user(
            phone=self.cleaned_data["phone"],  # normalized in clean_phone()
            password=self.cleaned_data["password1"],
            full_name=self.cleaned_data["full_name"],
            email=self.cleaned_data.get("email", ""),
        )


class LoginForm(forms.Form):
    """
    Форма входа по номеру телефона.
    Использует django.contrib.auth.authenticate.
    Кастомный backend должен поддерживать аутентификацию по телефону.
    """

    phone = forms.CharField(label="Телефон", max_length=24, validators=[phone_validator])
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        """
        Выполняет аутентификацию пользователя.
        В случае успеха:
            - сохраняет пользователя в cleaned_data["user"]
            - сохраняет нормализованный телефон в cleaned_data["phone"]
        В случае ошибки:
            - выбрасывает ValidationError.
        """
        cleaned = super().clean()
        phone = cleaned.get("phone")
        password = cleaned.get("password")
        if not phone or not password:
            return cleaned

        phone_norm = normalize_phone(phone)

        # Передаём телефон как username для совместимости с API authenticate
        user = authenticate(username=phone_norm, password=password)

        if user is None:
            raise forms.ValidationError("Неверный телефон или пароль.")

        cleaned["user"] = user
        cleaned["phone"] = phone_norm
        return cleaned
