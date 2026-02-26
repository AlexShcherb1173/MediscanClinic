from __future__ import annotations

from django.db import models


class City(models.Model):
    """
    City of presence for the clinic (contacts/schedule/branches).

    Stores basic contact details used across the website:
    phone number, address and an "active" flag to control visibility.
    """

    name = models.CharField(
        "Название",
        max_length=120,
        unique=True,
        help_text="Уникальное название города (например, Москва).",
    )
    phone = models.CharField(
        "Телефон",
        max_length=32,
        blank=True,
        help_text="Контактный телефон для города (опционально).",
    )
    address = models.CharField(
        "Адрес",
        max_length=255,
        blank=True,
        help_text="Адрес филиала/клиники в этом городе (опционально).",
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
        help_text="Показывать город на сайте.",
    )

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self) -> str:
        """Return a human-readable representation of the city."""
        return self.name


class SiteSettings(models.Model):
    """
    Global site configuration (singleton-like model).

    Intended to store a single row with project-wide settings:
    site title, contacts, legal information, integrations.
    """

    site_name = models.CharField(
        "Название сайта",
        max_length=120,
        default="Mediscan",
        help_text="Название, отображаемое в шапке/SEO (по умолчанию Mediscan).",
    )
    telegram_bot_url = models.URLField(
        "Ссылка на Telegram-бота",
        blank=True,
        help_text="URL на Telegram-бота/чат (опционально).",
    )
    email = models.EmailField(
        "Email",
        blank=True,
        help_text="Контактный email (опционально).",
    )
    legal_info = models.TextField(
        "Юридическая информация",
        blank=True,
        help_text="Реквизиты, ОГРН/ИНН, политика и т.п. (опционально).",
    )

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        """Return a label for admin display."""
        return "Site settings"


class License(models.Model):
    """
    License/certificate entity shown on the site.

    Stores a file (PDF or image) and an optional preview image.
    Visibility and ordering are controlled via `is_active` and `sort_order`.
    """

    title = models.CharField("Название", max_length=160)
    file = models.FileField(
        "Файл (PDF/изображение)",
        upload_to="licenses/",
        help_text="Основной файл лицензии/сертификата.",
    )
    preview = models.ImageField(
        "Превью (опционально)",
        upload_to="licenses/previews/",
        blank=True,
        null=True,
        help_text="Картинка-превью для списка (если нужно).",
    )

    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=100)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Лицензия/сертификат"
        verbose_name_plural = "Лицензии/сертификаты"
        ordering = ("sort_order", "-created_at")

    def __str__(self) -> str:
        """Return the license title."""
        return self.title