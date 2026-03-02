"""
Конфигурация Celery для проекта MediscanClinic.

Назначение:
- подключение Django-настроек (через namespace CELERY_);
- автоматический поиск tasks.py во всех INSTALLED_APPS;
- создание глобального экземпляра Celery-приложения `app`.

Этот модуль должен импортироваться в config/__init__.py,
чтобы Celery корректно инициализировался вместе с Django.
"""

import os

from celery import Celery


# -----------------------------------------------------------------------------
# Настройка DJANGO_SETTINGS_MODULE
# -----------------------------------------------------------------------------
# По умолчанию используется базовый модуль настроек.
# В production рекомендуется переопределять через переменную окружения:
#   DJANGO_SETTINGS_MODULE=config.settings.prod
# -----------------------------------------------------------------------------

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")


# -----------------------------------------------------------------------------
# Создание экземпляра Celery
# -----------------------------------------------------------------------------

app = Celery("config")

# Загружаем настройки Django, начинающиеся с CELERY_
# Например: CELERY_BROKER_URL, CELERY_BEAT_SCHEDULE и т.д.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически ищем tasks.py во всех приложениях из INSTALLED_APPS
app.autodiscover_tasks()