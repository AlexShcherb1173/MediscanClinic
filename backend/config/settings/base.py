from pathlib import Path
import environ
import os
from dotenv import load_dotenv
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # -> backend/

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

# читаем .env из корня проекта (рядом с requirements.txt)
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost", "testserver"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
   ]

INSTALLED_APPS += [
    "apps.core",
    "apps.pages",
    "apps.promos",
    "apps.services",
    "apps.staff",
    "apps.appointments",
    "apps.patients",
    "apps.contacts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # важен порядок (после Security)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # backend/templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.services.context_processors.popular_services",
                "apps.core.context_processors.core_context",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

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

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Если используешь WhiteNoise (обычно для прод):
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CELERY_BROKER_URL = "redis://127.0.0.1:6379/1"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/2"

CELERY_TASK_ALWAYS_EAGER = False  # в проде False, в тестах можно True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # Europe/Amsterdam

CELERY_BEAT_SCHEDULE = {
    "appointments-reminders-every-5-min": {
        "task": "apps.appointments.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*/5"),
    },
}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Куда слать: твой user id или chat id группы (например -100123...)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID","")

EMAIL_BACKEND = os.getenv("SMTP_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def _env_str(name: str, default: str = "") -> str:
    v = os.getenv(name, default)
    # защита от случайных tuple/list
    if isinstance(v, (tuple, list)):
        v = v[0] if v else default
    return str(v).strip()

DEFAULT_FROM_EMAIL = _env_str("DEFAULT_FROM_EMAIL", "lenovo2015549@gmail.com")
CONTACTS_ADMIN_EMAIL = _env_str("CONTACTS_ADMIN_EMAIL", DEFAULT_FROM_EMAIL)
