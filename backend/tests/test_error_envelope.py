"""Tests for the standard API error envelope."""

from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.test import APIRequestFactory

from common.exceptions import api_exception_handler


class Conflict(APIException):
    status_code = 409
    default_detail = "The request conflicts with the current state."
    default_code = "conflict"


def handle(exc):
    request = APIRequestFactory().get("/api/v1/example/")
    return api_exception_handler(exc, {"request": request, "view": None})


def test_validation_error_uses_envelope():
    response = handle(ValidationError({"sku": ["A product with this SKU already exists."]}))
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["details"]["errors"] == {
        "sku": ["A product with this SKU already exists."]
    }


def test_authentication_error_uses_envelope():
    response = handle(NotAuthenticated())
    assert response.status_code == 401
    body = response.data["error"]
    assert body["code"] == "authentication_required"
    assert body["message"]
    assert body["details"] == {}


def test_permission_error_uses_envelope():
    response = handle(PermissionDenied())
    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"


def test_not_found_uses_envelope():
    response = handle(NotFound())
    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_found"


def test_conflict_uses_envelope():
    response = handle(Conflict())
    assert response.status_code == 409
    assert response.data["error"]["code"] == "conflict"


def test_throttled_uses_envelope():
    response = handle(Throttled())
    assert response.status_code == 429
    assert response.data["error"]["code"] == "rate_limited"


def test_unhandled_exception_hides_details():
    response = handle(Exception("boom: secret-token-xyz"))
    assert response.status_code == 500
    body = response.data["error"]
    assert body["code"] == "internal_server_error"
    assert "secret-token-xyz" not in str(response.data)
