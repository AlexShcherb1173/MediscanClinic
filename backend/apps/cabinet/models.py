from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    telegram_chat_id = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return f"Profile: {self.user}"
