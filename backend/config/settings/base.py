"""
Базовые настройки Django-проекта MediscanClinic.

Этот модуль содержит общие настройки для всех окружений (dev/prod/test):
- пути проекта и загрузка переменных окружения (.env);
- список приложений и middleware;
- шаблоны и URL-конфигурация;
- база данных, static/media;
- интеграции: Celery, Telegram, Email (SMTP), Яндекс.Карты, SMS;
- базовые настройки логирования.

Окружение-специфичные переопределения должны находиться в:
- config/settings/dev.py
- config/settings/prod.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import environ
from celery.schedules import crontab

# -----------------------------------------------------------------------------
# Пути проекта и переменные окружения
# -----------------------------------------------------------------------------

# Корень backend/ (где лежат manage.py, apps/, config/, templates/, static/ и т.д.)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Инициализация env (django-environ)
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

# Читаем .env из корня репозитория (на уровень выше backend/)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env("DJANGO_DEBUG")


if DEBUG:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Защита от запуска prod без реального SECRET_KEY
if not DEBUG and SECRET_KEY == "django-insecure-dev-key":
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production (not default)")

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "testserver"],
)


def _env_str(name: str, default: str = "") -> str:
    """
    Прочитать переменную окружения как «чистую» строку.

    Иногда хостинги/пайплайны могут передать значение как tuple/list
    (например, при ошибочной конфигурации). Функция нормализует это поведение.

    Args:
        name: Имя переменной окружения.
        default: Значение по умолчанию, если переменная отсутствует.

    Returns:
        Обрезанная строка (strip).
    """
    value = os.getenv(name, default)
    if isinstance(value, (tuple, list)):
        value = value[0] if value else default
    return str(value).strip()


# -----------------------------------------------------------------------------
# Приложения
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django contrib
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Приложения проекта
    "apps.pages",
    "apps.promos",
    "apps.services",
    "apps.staff",
    "apps.appointments",
    "apps.patients",
    "apps.contacts",
    "apps.results",
    "apps.cabinet",
    "apps.accounts",
]

# Для django.contrib.sites (если используется)
SITE_ID = 1

# -----------------------------------------------------------------------------
# Аутентификация
# -----------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "apps.accounts.backends.PhoneBackend",
)

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "cabinet:dashboard"
LOGOUT_REDIRECT_URL = "pages:home"

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -----------------------------------------------------------------------------
# URL / Templates
# -----------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # Django стандартные
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Контекстные процессоры проекта
                "apps.services.context_processors.popular_services",
                "apps.cabinet.context_processors.cabinet_badges",
                "apps.accounts.context_processors.lk_user_data",
                "apps.staff.context_processors.doctor_slider_items",
            ],
        },
    }
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -----------------------------------------------------------------------------
# База данных
# -----------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="mediscan_db"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# -----------------------------------------------------------------------------
# i18n / TZ
# -----------------------------------------------------------------------------

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: сжатие + манифест (подходит для prod)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# В тестах манифест иногда мешает (например, при отсутствии collectstatic)
if "test" in sys.argv:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------------------------------------------------------
# Celery
# -----------------------------------------------------------------------------

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")

CELERY_TASK_ALWAYS_EAGER = False
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Периодические задачи Celery Beat
CELERY_BEAT_SCHEDULE = {
    "appointments-reminders-every-5-min": {
        # Важно: имя таски должно совпадать с реальным import path
        "task": "apps.appointments.tasks.send_appointments_reminders",
        "schedule": crontab(minute="*/5"),
    },
}

# -----------------------------------------------------------------------------
# Telegram
# -----------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Базовый URL Telegram API. Токен добавляется на уровне клиента.
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org")

# -----------------------------------------------------------------------------
# Email (SMTP)
# -----------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv(
    "SMTP_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# От кого отправляем письма по умолчанию (и куда слать админские письма по контактам)
DEFAULT_FROM_EMAIL = _env_str("DEFAULT_FROM_EMAIL", "lenovo2015549@gmail.com")
CONTACTS_ADMIN_EMAIL = _env_str("CONTACTS_ADMIN_EMAIL", DEFAULT_FROM_EMAIL)

# -----------------------------------------------------------------------------
# Яндекс.Карты / SMS
# -----------------------------------------------------------------------------

YMAPS_API_KEY = os.getenv("YMAPS_API_KEY", "")

SMS_RU_API_ID = os.getenv("SMS_RU_API_ID", "")
SMS_SENDER = os.getenv("SMS_SENDER", "")
SMS_RU_TEST = os.getenv("SMS_RU_TEST", "0") == "1"

# -----------------------------------------------------------------------------
# Логирование
# -----------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Вывод в консоль (удобно для Docker/systemd)
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        # Логи SMS-отправки (по необходимости расширишь на другие модули)
        "appointments.sms": {"handlers": ["console"], "level": "INFO"},
    },
}