"""Shared cross-module helpers. Business rules live in apps/, not here."""

from django.utils import timezone


def utcnow():
    """Return the current timezone-aware UTC datetime."""
    return timezone.now()
