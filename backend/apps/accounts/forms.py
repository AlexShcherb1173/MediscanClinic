"""
Forms for accounts application.

Includes:
- RegisterForm: phone-based registration with password confirmation
- LoginForm: phone-based authentication using custom backend
"""

from __future__ import annotations

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
    """
    Simple registration form (phone + password + full name).

    Validation:
        - phone is normalized and must be unique
        - password1 and password2 must match
    """

    full_name = forms.CharField(label="ФИО", min_length=2, max_length=255)
    phone = forms.CharField(
        label="Телефон", max_length=24, validators=[phone_validator]
    )
    email = forms.EmailField(
        label="Email", required=False, validators=[EmailValidator()]
    )
    password1 = forms.CharField(
        label="Пароль", widget=forms.PasswordInput, min_length=6
    )
    password2 = forms.CharField(
        label="Повтор пароля", widget=forms.PasswordInput, min_length=6
    )

    def clean_phone(self) -> str:
        """Normalize phone and ensure uniqueness."""
        phone = normalize_phone(self.cleaned_data["phone"])
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "Пользователь с таким телефоном уже существует."
            )
        return phone

    def clean(self):
        """Ensure passwords match."""
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned

    def save(self) -> User:
        """Create user using UserManager."""
        return User.objects.create_user(
            phone=self.cleaned_data["phone"],  # normalized in clean_phone()
            password=self.cleaned_data["password1"],
            full_name=self.cleaned_data["full_name"],
            email=self.cleaned_data.get("email", ""),
        )


class LoginForm(forms.Form):
    """
    Login form for phone-based authentication.

    Uses django.contrib.auth.authenticate; custom backend should support phone.
    """

    phone = forms.CharField(
        label="Телефон", max_length=24, validators=[phone_validator]
    )
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        """Authenticate user and store it in cleaned_data['user']."""
        cleaned = super().clean()
        phone = cleaned.get("phone")
        password = cleaned.get("password")
        if not phone or not password:
            return cleaned

        phone_norm = normalize_phone(phone)

        # Pass phone as username for compatibility with auth backend API
        user = authenticate(username=phone_norm, password=password)

        if user is None:
            raise forms.ValidationError("Неверный телефон или пароль.")

        cleaned["user"] = user
        cleaned["phone"] = phone_norm
        return cleaned
