from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError



from decimal import Decimal


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

class ServiceCategory(models.Model):
    name = models.CharField("Название", max_length=150)
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        related_name="services",
        on_delete=models.CASCADE,
    )
    name = models.CharField("Название", max_length=255)
    price_from = models.DecimalField("Цена от", max_digits=10, decimal_places=2)
    price_to = models.DecimalField(
        "Цена до",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.price_to is not None and self.price_to < self.price_from:
            raise ValidationError({"price_to": "Цена до не может быть меньше цены от."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)