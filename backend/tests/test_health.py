"""Foundation tests: health check and the standard error envelope."""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_health_returns_ok_when_database_is_reachable(api_client):
    response = api_client.get(reverse("health"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "database": "connected"}


def test_unknown_route_uses_error_envelope(api_client):
    response = api_client.get("/api/v1/does-not-exist/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]
