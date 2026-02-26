"""
Settings package entrypoint.

Selects settings module (dev/prod) based on environment variable.
Default: dev.
"""

import os

env = os.getenv("DJANGO_ENV", "dev").lower()

if env == "prod":
    from .prod import *  # noqa
else:
    from .dev import *  # noqa