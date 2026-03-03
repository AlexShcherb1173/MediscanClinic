"""
Модели приложения акций (promos).
Promo — маркетинговая сущность, отображаемая на главной странице
и на страницах акций.
Поддерживает:
- период показа (starts_at / ends_at);
- флаг активности;
- ручную сортировку;
- связь с услугами.
"""

from __future__ import annotations

from apps.services.models import Service
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Promo(models.Model):
    """
    Модель акции (маркетинговая кампания / спецпредложение).
    Используется для отображения баннеров и спецпредложений на сайте.
    Поля:
        title: Основной заголовок акции.
        slug: Уникальный идентификатор для формирования URL
              (автоматически генерируется из title).
        badge: Короткий бейдж (например: «Скидка», «Чек-ап»).
        subtitle: Краткий дополнительный текст.
        description: Подробное описание (текст или HTML).
        image: Изображение акции.
        cta_text: Текст кнопки действия.
        cta_url: Ссылка кнопки (внутренняя или внешняя).
        services: Связанные услуги, входящие в акцию.
        starts_at / ends_at: Период отображения акции.
        is_active: Ручной флаг включения/отключения.
        sort_order: Порядок сортировки в списках.
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
        """
        Возвращает заголовок акции
        для отображения в админке и интерфейсе.
        """
        return self.title

    def save(self, *args, **kwargs):
        """
        Автоматически генерирует уникальный slug из title,
        если он не задан вручную.
        Стратегия:
            - выполняется slugify(title) с ограничением длины;
            - при конфликте добавляется суффикс "-2", "-3" и т.д.;
            - проверка уникальности выполняется с исключением текущего объекта.
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
        Определяет, должна ли акция отображаться в текущий момент.
        Условия:
            - is_active=True;
            - если задан starts_at — текущее время >= starts_at;
            - если задан ends_at — текущее время <= ends_at.
        Возвращает:
            bool: True, если акция актуальна и должна быть показана.
        """
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True
