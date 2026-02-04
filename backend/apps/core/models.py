from django.db import models


class City(models.Model):
    name = models.CharField(max_length=120, unique=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"

    def __str__(self) -> str:
        return self.name


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=120, default="Mediscan")
    telegram_bot_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    legal_info = models.TextField(blank=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return "Site settings"

class License(models.Model):
    title = models.CharField("Название", max_length=160)
    file = models.FileField("Файл (PDF/изображение)", upload_to="licenses/")
    preview = models.ImageField("Превью (опционально)", upload_to="licenses/previews/", blank=True, null=True)

    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=100)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Лицензия/сертификат"
        verbose_name_plural = "Лицензии/сертификаты"
        ordering = ("sort_order", "-created_at")

    def __str__(self) -> str:
        return self.title