"""Celery application. Task modules land here as milestones deliver them."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("depotledger")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
