"""
Модели статических (контентных) страниц.
Предоставляет простую CMS-подобную модель Page
с маршрутизацией по slug и флагом публикации.
"""

from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    """
    Модель статической страницы.
    Используется для отображения информационных разделов сайта
    (например: «О компании», «Политика конфиденциальности», «Условия»).
    Поля:
        title: Заголовок страницы.
        slug: Уникальный идентификатор для формирования URL.
        content: HTML- или текстовый контент страницы.
        is_published: Флаг видимости страницы на сайте.
    """

    title = models.CharField("Заголовок", max_length=200)
    slug = models.SlugField("Слаг", max_length=220, unique=True)
    content = models.TextField("Контент", blank=True)
    is_published = models.BooleanField("Опубликована", default=True)

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    def save(self, *args, **kwargs):
        """
        Автоматически генерирует slug из заголовка,
        если он не был указан вручную.
        Использует slugify с поддержкой Unicode.
        """
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Возвращает заголовок страницы
        для отображения в админке и логах.
        """
        return self.title
