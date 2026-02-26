"""
Base Django settings for MediscanClinic project.

This module contains shared settings for all environments (dev/prod/test):
- paths, env loading
- installed apps and middleware
- templates and URL configuration
- database, static/media
- integrations: Celery, Telegram, Email, Yandex Maps, SMS
- logging defaults

Environment-specific overrides should be defined in:
- config/settings/dev.py
- config/settings/prod.py
"""

from __future__ import annotations

import os
from pathlib import Path

import environ
from celery.schedules import crontab

# -----------------------------------------------------------------------------
# Paths & environment
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> backend/

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

# Read .env from project root (one level above backend/)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env("DJANGO_DEBUG")

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "testserver"],
)


def _env_str(name: str, default: str = "") -> str:
    """
    Read env variable as a clean string.

    Some deploy platforms may expose env values as list/tuple; normalize them.
    """
    value = os.getenv(name, default)
    if isinstance(value, (tuple, list)):
        value = value[0] if value else default
    return str(value).strip()


# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "apps.core",
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

SITE_ID = 1

# -----------------------------------------------------------------------------
# Authentication
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
# URLs / Templates
# -----------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Project context processors
                "apps.services.context_processors.popular_services",
                "apps.core.context_processors.core_context",
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
# Database
# -----------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
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
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static / Media
# -----------------------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------------------------------------------------------
# Celery
# -----------------------------------------------------------------------------

CELERY_BROKER_URL = "redis://127.0.0.1:6379/1"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/2"

CELERY_TASK_ALWAYS_EAGER = False
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "appointments-reminders-every-5-min": {
        "task": "apps.appointments.tasks.send_appointment_reminders",
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

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# -----------------------------------------------------------------------------
# Email (SMTP)
# -----------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv("SMTP_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")

DEFAULT_FROM_EMAIL = _env_str("DEFAULT_FROM_EMAIL", "lenovo2015549@gmail.com")
CONTACTS_ADMIN_EMAIL = _env_str("CONTACTS_ADMIN_EMAIL", DEFAULT_FROM_EMAIL)

# -----------------------------------------------------------------------------
# Yandex Maps / SMS
# -----------------------------------------------------------------------------

YMAPS_API_KEY = os.getenv("YMAPS_API_KEY", "")

SMS_RU_API_ID = os.getenv("SMS_RU_API_ID", "")
SMS_SENDER = os.getenv("SMS_SENDER", "")
SMS_RU_TEST = os.getenv("SMS_RU_TEST", "0") == "1"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "appointments.sms": {"handlers": ["console"], "level": "INFO"},
    },
}