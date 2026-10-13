"""Tests for warehouses, storage locations, customers, and suppliers."""

import pytest
from django.contrib.auth.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(username="clerk", password="x", is_active=True)


@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def warehouse(authed_client):
    response = authed_client.post(
        "/api/v1/warehouses/", {"code": "ACC-01", "name": "Accra Central"}, format="json"
    )
    assert response.status_code == 201, response.data
    return response.data


def test_duplicate_warehouse_code_is_rejected(authed_client, warehouse):
    duplicate = authed_client.post(
        "/api/v1/warehouses/", {"code": "ACC-01", "name": "Somewhere else"}, format="json"
    )
    assert duplicate.status_code == 400
    assert duplicate.data["error"]["code"] == "validation_error"


def test_nested_location_create_and_list(authed_client, warehouse):
    created = authed_client.post(
        f"/api/v1/warehouses/{warehouse['id']}/locations/",
        {"code": "A-01", "location_type": "storage"},
        format="json",
    )
    assert created.status_code == 201, created.data
    assert str(created.data["warehouse_id"]) == warehouse["id"]

    listed = authed_client.get(f"/api/v1/warehouses/{warehouse['id']}/locations/")
    assert listed.status_code == 200
    assert listed.data["count"] == 1

    retrieved = authed_client.get(f"/api/v1/locations/{created.data['id']}/")
    assert retrieved.status_code == 200
    assert retrieved.data["code"] == "A-01"


def test_location_code_unique_per_warehouse(authed_client, warehouse):
    other = authed_client.post(
        "/api/v1/warehouses/", {"code": "KUM-01", "name": "Kumasi"}, format="json"
    ).data

    assert (
        authed_client.post(
            f"/api/v1/warehouses/{warehouse['id']}/locations/", {"code": "A-01"}, format="json"
        ).status_code
        == 201
    )
    duplicate = authed_client.post(
        f"/api/v1/warehouses/{warehouse['id']}/locations/", {"code": "A-01"}, format="json"
    )
    assert duplicate.status_code == 400
    assert duplicate.data["error"]["code"] == "validation_error"

    same_code_elsewhere = authed_client.post(
        f"/api/v1/warehouses/{other['id']}/locations/", {"code": "A-01"}, format="json"
    )
    assert same_code_elsewhere.status_code == 201


def test_location_for_unknown_warehouse_is_not_found(authed_client):
    response = authed_client.get(
        "/api/v1/warehouses/00000000-0000-0000-0000-000000000000/locations/"
    )
    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_found"


def test_customer_create_duplicate_and_archive(authed_client):
    created = authed_client.post(
        "/api/v1/customers/",
        {"customer_code": "CUST-001", "name": "Acme Markets", "email": "buy@acme.example"},
        format="json",
    )
    assert created.status_code == 201, created.data

    duplicate = authed_client.post(
        "/api/v1/customers/", {"customer_code": "CUST-001", "name": "Clone"}, format="json"
    )
    assert duplicate.status_code == 400

    archived = authed_client.patch(
        f"/api/v1/customers/{created.data['id']}/", {"is_active": False}, format="json"
    )
    assert archived.status_code == 200
    assert archived.data["archived_at"] is not None


def test_supplier_create_duplicate_and_archive(authed_client):
    created = authed_client.post(
        "/api/v1/suppliers/", {"supplier_code": "SUP-001", "name": "Grain Co-op"}, format="json"
    )
    assert created.status_code == 201, created.data

    duplicate = authed_client.post(
        "/api/v1/suppliers/", {"supplier_code": "SUP-001", "name": "Clone"}, format="json"
    )
    assert duplicate.status_code == 400

    archived = authed_client.patch(
        f"/api/v1/suppliers/{created.data['id']}/", {"is_active": False}, format="json"
    )
    assert archived.status_code == 200
    assert archived.data["archived_at"] is not None
