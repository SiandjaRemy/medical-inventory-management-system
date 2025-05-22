from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime:s} {name} {module}.py (line {lineno:d}) {funcName} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime:s} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "django_api.log",
            "formatter": "verbose",
        },
        "error_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "django_api.log",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": True,
        },
    },
}


