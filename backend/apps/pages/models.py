"""
Models for static/content pages.

Provides a simple CMS-like Page model
with slug-based routing and publication flag.
"""

from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    """
    Static content page model.

    Used for rendering informational pages
    (e.g. About, Privacy Policy, Terms).

    Attributes:
        title: Page title.
        slug: Unique URL identifier.
        content: HTML or text content.
        is_published: Controls page visibility.
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
        Auto-generate slug from title if not provided.

        Uses Django's slugify with Unicode support.
        """
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return page title for admin representation."""
        return self.title
