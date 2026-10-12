"""Test settings. Mirror production error handling; keep execution fast."""

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = ["testserver", "localhost"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CELERY_TASK_ALWAYS_EAGER = True
