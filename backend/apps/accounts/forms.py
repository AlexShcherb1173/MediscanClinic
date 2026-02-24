from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator, EmailValidator

from .utils import normalize_phone

User = get_user_model()

phone_validator = RegexValidator(
    regex=r"^\+?\d[\d\s\-\(\)]{8,20}$",
    message="Введите телефон в формате +79990000000 (можно пробелы/скобки/дефисы).",
)

class RegisterForm(forms.Form):
    full_name = forms.CharField(label="ФИО", min_length=2, max_length=255)
    phone = forms.CharField(label="Телефон", max_length=24, validators=[phone_validator])
    email = forms.EmailField(label="Email", required=False, validators=[EmailValidator()])
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput, min_length=6)

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned

    def save(self) -> User:
        return User.objects.create_user(
            phone=self.cleaned_data["phone"],              # уже нормализован в clean_phone()
            password=self.cleaned_data["password1"],
            full_name=self.cleaned_data["full_name"],
            email=self.cleaned_data.get("email", ""),
        )

class LoginForm(forms.Form):
    phone = forms.CharField(label="Телефон", max_length=24, validators=[phone_validator])
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get("phone")
        password = cleaned.get("password")
        if not phone or not password:
            return cleaned

        phone_norm = normalize_phone(phone)

        # ✅ ВАЖНО: передаём как username (или phone — теперь backend поддержит оба)
        user = authenticate(username=phone_norm, password=password)

        if user is None:
            raise forms.ValidationError("Неверный телефон или пароль.")

        cleaned["user"] = user
        cleaned["phone"] = phone_norm
        return cleaned