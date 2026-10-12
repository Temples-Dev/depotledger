"""Tests for shared permission bases."""

import pytest
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.test import APIRequestFactory

from common.permissions import ActiveUserPermission


def request_with(user):
    request = APIRequestFactory().get("/api/v1/example/")
    request.user = user
    return request


def test_anonymous_user_is_denied():
    permission = ActiveUserPermission()
    assert permission.has_permission(request_with(AnonymousUser()), None) is False


@pytest.mark.django_db
def test_inactive_user_is_denied():
    user = User.objects.create_user(username="inactive", password="x", is_active=False)
    permission = ActiveUserPermission()
    assert permission.has_permission(request_with(user), None) is False


@pytest.mark.django_db
def test_active_user_is_allowed():
    user = User.objects.create_user(username="active", password="x", is_active=True)
    permission = ActiveUserPermission()
    assert permission.has_permission(request_with(user), None) is True
