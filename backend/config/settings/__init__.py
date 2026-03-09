"""
Точка входа пакета настроек Django.
Модуль выбирает конфигурацию проекта в зависимости от переменной
окружения DJANGO_ENV.

Поддерживаемые окружения:
    - dev  — разработка (по умолчанию)
    - prod — production
Если переменная DJANGO_ENV не задана, используется dev.
"""

from __future__ import annotations

import os

# Определяем окружение (dev по умолчанию)
env = os.getenv("DJANGO_ENV", "dev").lower()

if env == "prod":
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
