"""Local development settings. SQLite by default; set DB_ENGINE for Postgres."""

import os

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS += ["localhost", "127.0.0.1"]

if os.environ.get("DB_ENGINE", "django.db.backends.sqlite3") == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
