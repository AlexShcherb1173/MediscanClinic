from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Promo(models.Model):
    title = models.CharField("Заголовок", max_length=160)
    slug = models.SlugField("Slug", max_length=180, unique=True, blank=True)
    badge = models.CharField("Бейдж", max_length=32, blank=True, help_text="Напр.: Скидка, Чек-ап, Ночь")
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
        return self.title

    def save(self, *args, **kwargs):
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
        """Акция активна и попадает в период показа (если задан)."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True