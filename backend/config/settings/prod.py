"""
Настройки Django для production-окружения (prod).

Основаны на config/settings/base.py.

Особенности:
- DEBUG отключён;
- включены основные security-настройки;
- предполагается запуск за reverse-proxy (например, Nginx);
- используется HTTPS.
"""

from .base import *  # noqa: F403,F401

# -----------------------------------------------------------------------------
# Основные параметры production
# -----------------------------------------------------------------------------

# В production DEBUG всегда выключен.
DEBUG = False

# Если проект работает за Nginx / Traefik / Yandex Cloud LB,
# заголовок X-Forwarded-Proto сообщает Django,
# что реальный протокол клиента был HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# -----------------------------------------------------------------------------
# Безопасность
# -----------------------------------------------------------------------------

# Защита от XSS (дополнительный заголовок браузеру)
SECURE_BROWSER_XSS_FILTER = True

# Запрет MIME-sniffing (защита от подмены типа контента)
SECURE_CONTENT_TYPE_NOSNIFF = True

# Cookies доступны только по HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Автоматический редирект HTTP → HTTPS
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"


# -----------------------------------------------------------------------------
# Рекомендуемые дополнительные настройки (по желанию)
# -----------------------------------------------------------------------------
#
# Ниже — безопасные параметры, которые обычно включаются в production.
# При необходимости можно раскомментировать.
#
# # HSTS (строгий HTTPS, браузер запоминает)
# SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 год
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
#
# # Запрет встраивания сайта в iframe (кликджекинг)
# X_FRAME_OPTIONS = "DENY"
#
# # Ограничение CSRF доверенных доменов (если есть внешние формы)
# # CSRF_TRUSTED_ORIGINS = ["https://yourdomain.com"]
#
