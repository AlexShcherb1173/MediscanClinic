"""
WSGI-конфигурация проекта MediscanClinic.

Экспортирует WSGI-приложение как переменную уровня модуля `application`.

Используется WSGI-серверами (Gunicorn, uWSGI и др.) для:
- обработки HTTP-запросов в синхронном режиме;
- классического деплоя Django-приложения;
- запуска через systemd, Docker или PaaS.

В production обычно запускается через Gunicorn:
    gunicorn config.wsgi:application
"""

import os

from django.core.wsgi import get_wsgi_application


# -----------------------------------------------------------------------------
# Настройка DJANGO_SETTINGS_MODULE
# -----------------------------------------------------------------------------
# По умолчанию указываем dev-настройки.
# В production рекомендуется задавать переменную окружения:
#   DJANGO_SETTINGS_MODULE=config.settings.prod
#
# setdefault не перезапишет переменную,
# если она уже задана через окружение.
# -----------------------------------------------------------------------------

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.dev",
)


# -----------------------------------------------------------------------------
# Инициализация WSGI-приложения Django
# -----------------------------------------------------------------------------

application = get_wsgi_application()