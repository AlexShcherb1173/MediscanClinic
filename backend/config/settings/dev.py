from .base import *  # noqa

DEBUG = True
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "appointments": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}