"""
Models for services application.

Contains:
- ServiceCategory — groups services
- Service — medical service with pricing, visibility and featured flags
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class ServiceCategory(models.Model):
    """
    Category for grouping services.

    Attributes:
        name: Display name of the category.
        slug: Unique URL identifier.
        order: Sorting order in listings.
        is_active: Controls visibility on the website.
    """

    name = models.CharField("Название", max_length=150)
    slug = models.SlugField("Слаг", unique=True)
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return category name for admin representation."""
        return self.name


class Service(models.Model):
    """
    Medical service entity.

    Includes pricing range, publication flag,
    and featured configuration for homepage display.
    """

    category = models.ForeignKey(
        ServiceCategory,
        related_name="services",
        on_delete=models.CASCADE,
        verbose_name="Категория",
    )

    name = models.CharField("Название", max_length=255)

    slug = models.SlugField("Слаг", unique=True, blank=True)

    description = models.TextField("Описание", blank=True)

    price_from = models.DecimalField(
        "Цена от",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    price_to = models.DecimalField(
        "Цена до",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    is_active = models.BooleanField("Активна", default=True)

    # Featured services (homepage block)
    is_featured = models.BooleanField(
        "Показывать на главной",
        default=False,
        db_index=True,
    )

    featured_order = models.PositiveIntegerField(
        "Порядок на главной",
        default=0,
        db_index=True,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        indexes = [
            models.Index(fields=("is_active", "is_featured")),
        ]

    def __str__(self) -> str:
        """Return service name."""
        return self.name

    def clean(self):
        """
        Validate pricing logic.

        Ensures:
            - price_to is not less than price_from
        """
        super().clean()

        if self.price_to is not None and self.price_to < self.price_from:
            raise ValidationError({"price_to": "Цена до не может быть меньше цены от."})

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
