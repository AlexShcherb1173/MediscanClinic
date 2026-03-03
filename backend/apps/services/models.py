"""
Модели приложения услуг (services).
Содержит:
- ServiceCategory — категории для группировки услуг;
- Service — медицинская услуга с ценами, флагами публикации
  и настройками отображения на главной странице.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class ServiceCategory(models.Model):
    """
    Модель категории услуг.
    Используется для логической группировки медицинских услуг
    и управления их отображением на сайте.
    Поля:
        name: Название категории.
        slug: Уникальный идентификатор для URL.
        order: Порядок сортировки в списках.
        is_active: Флаг отображения категории на сайте.
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
        Автоматически генерирует slug из name,
        если он не был задан вручную.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Возвращает название категории
        для отображения в админке и интерфейсе.
        """
        return self.name


class Service(models.Model):
    """
    Модель медицинской услуги.
    Хранит описание услуги, диапазон цен,
    флаги активности и настройки отображения
    на главной странице сайта.
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
        """
        Возвращает название услуги
        для отображения в админке и списках.
        """
        return self.name

    def clean(self):
        """
        Валидация бизнес-логики цен.
        Проверяет:
            - если указано price_to, оно не может быть меньше price_from.
        Вызывает ValidationError при нарушении правила.
        """
        super().clean()

        if self.price_to is not None and self.price_to < self.price_from:
            raise ValidationError({"price_to": "Цена до не может быть меньше цены от."})

    def save(self, *args, **kwargs):
        """
        Автоматически генерирует slug из name,
        если он не был задан вручную.
        Используется slugify с поддержкой Unicode.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
