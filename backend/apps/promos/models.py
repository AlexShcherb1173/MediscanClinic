"""
Models for promos application.

Promo is a marketing entity displayed on homepage and promo pages.
Supports:
- optional display period (starts_at / ends_at)
- active flag
- ordering
- relation to services
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.services.models import Service


class Promo(models.Model):
    """
    Promo model (marketing campaign / special offer).

    Attributes:
        title: main title
        slug: unique identifier for URLs (auto-generated from title)
        badge: short label (e.g. "Скидка", "Чек-ап")
        subtitle: short secondary text
        description: detailed text (plain or HTML)
        image: optional promo image
        cta_text: button label
        cta_url: button link (internal or external)
        services: related services included in promo
        starts_at/ends_at: optional visibility window
        is_active: manual switch for visibility
        sort_order: manual ordering
    """

    title = models.CharField("Заголовок", max_length=160)
    slug = models.SlugField("Slug", max_length=180, unique=True, blank=True)
    badge = models.CharField(
        "Бейдж", max_length=32, blank=True, help_text="Напр.: Скидка, Чек-ап, Ночь"
    )
    subtitle = models.CharField("Подзаголовок", max_length=220, blank=True)
    description = models.TextField("Описание", blank=True)

    image = models.ImageField("Картинка", upload_to="promos/", blank=True, null=True)

    cta_text = models.CharField("Текст кнопки", max_length=48, default="Подробнее")
    cta_url = models.CharField(
        "Ссылка кнопки",
        max_length=255,
        blank=True,
        help_text="Напр.: /services/?q=МРТ или https://…",
    )

    services = models.ManyToManyField(
        Service,
        verbose_name="Услуги по акции",
        related_name="promos",
        blank=True,
    )

    starts_at = models.DateTimeField("Начало", blank=True, null=True)
    ends_at = models.DateTimeField("Окончание", blank=True, null=True)

    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=100)

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"
        ordering = ("sort_order", "-created_at")

    def __str__(self) -> str:
        """Human-readable representation (admin/UI)."""
        return self.title

    def save(self, *args, **kwargs):
        """
        Auto-generate unique slug from title if not provided.

        Strategy:
        - slugify title (truncated)
        - if exists, append "-2", "-3", ... until unique
        """
        if not self.slug:
            base = slugify(self.title)[:170] or "promo"
            slug = base
            i = 2
            while Promo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_current(self) -> bool:
        """
        Return True if promo should be shown now.

        Conditions:
        - is_active is True
        - if starts_at is set, now must be >= starts_at
        - if ends_at is set, now must be <= ends_at
        """
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True
