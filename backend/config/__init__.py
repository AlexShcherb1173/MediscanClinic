"""
Project package initialization.

Exposes Celery app as `celery_app` for Django/Celery autodiscovery.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)