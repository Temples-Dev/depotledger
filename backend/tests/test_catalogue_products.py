"""Tests for catalogue products, categories, and barcodes."""

import pytest
from django.contrib.auth.models import User

from apps.catalogue.models import Product, ProductCategory


@pytest.fixture
def user(db):
    return User.objects.create_user(username="clerk", password="x", is_active=True)


@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def category(db):
    return ProductCategory.objects.create(name="Grains")


def product_payload(**overrides):
    payload = {
        "sku": "RICE-25KG",
        "name": "Rice, 25 kg",
        "description": "25 kg bag of rice",
        "base_unit": "bag",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def test_unauthenticated_list_is_rejected(api_client):
    response = api_client.get("/api/v1/products/")
    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"


def test_create_and_retrieve_product(authed_client, category):
    created = authed_client.post(
        "/api/v1/products/", product_payload(category_id=str(category.id)), format="json"
    )
    assert created.status_code == 201, created.data
    assert created.data["sku"] == "RICE-25KG"
    assert str(created.data["category_id"]) == str(category.id)

    retrieved = authed_client.get(f"/api/v1/products/{created.data['id']}/")
    assert retrieved.status_code == 200
    assert retrieved.data["base_unit"] == "bag"


def test_duplicate_sku_is_rejected(authed_client):
    first = authed_client.post("/api/v1/products/", product_payload(), format="json")
    assert first.status_code == 201
    duplicate = authed_client.post(
        "/api/v1/products/", product_payload(name="Other rice"), format="json"
    )
    assert duplicate.status_code == 400
    assert duplicate.data["error"]["code"] == "validation_error"


def test_unknown_category_is_rejected(authed_client):
    response = authed_client.post(
        "/api/v1/products/",
        product_payload(category_id="00000000-0000-0000-0000-000000000000"),
        format="json",
    )
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"


def test_deactivation_stamps_archived_at(authed_client):
    created = authed_client.post("/api/v1/products/", product_payload(), format="json")
    assert created.data["archived_at"] is None

    patched = authed_client.patch(
        f"/api/v1/products/{created.data['id']}/", {"is_active": False}, format="json"
    )
    assert patched.status_code == 200
    assert patched.data["is_active"] is False
    assert patched.data["archived_at"] is not None

    product = Product.objects.get(pk=created.data["id"])
    assert product.archived_at is not None


def test_product_cannot_be_deleted(authed_client):
    created = authed_client.post("/api/v1/products/", product_payload(), format="json")
    response = authed_client.delete(f"/api/v1/products/{created.data['id']}/")
    assert response.status_code == 405
    assert response.data["error"]["code"] == "method_not_allowed"
    assert Product.objects.filter(pk=created.data["id"]).exists()


def test_product_list_uses_collection_envelope(authed_client):
    for index in range(3):
        authed_client.post("/api/v1/products/", product_payload(sku=f"SKU-{index}"), format="json")
    response = authed_client.get("/api/v1/products/")
    assert response.status_code == 200
    assert set(response.data) == {"count", "next", "previous", "results"}
    assert response.data["count"] == 3


def test_product_search_and_active_filter(authed_client):
    authed_client.post("/api/v1/products/", product_payload(sku="RICE-25KG"), format="json")
    authed_client.post(
        "/api/v1/products/",
        product_payload(
            sku="BEANS-10KG", name="Beans", description="10 kg bag of beans", is_active=False
        ),
        format="json",
    )

    searched = authed_client.get("/api/v1/products/?search=rice")
    assert searched.data["count"] == 1

    active_only = authed_client.get("/api/v1/products/?is_active=true")
    assert active_only.data["count"] == 1
    assert active_only.data["results"][0]["sku"] == "RICE-25KG"


def test_category_cannot_reference_itself(authed_client, category):
    response = authed_client.patch(
        f"/api/v1/categories/{category.id}/", {"parent_id": str(category.id)}, format="json"
    )
    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"


def test_barcode_create_resolve_and_duplicate(authed_client):
    created = authed_client.post("/api/v1/products/", product_payload(), format="json")
    product_id = created.data["id"]

    barcode = authed_client.post(
        "/api/v1/barcodes/",
        {"product_id": product_id, "barcode": "6001234567890", "barcode_type": "EAN-13"},
        format="json",
    )
    assert barcode.status_code == 201, barcode.data

    resolved = authed_client.get("/api/v1/barcodes/6001234567890/")
    assert resolved.status_code == 200
    assert str(resolved.data["product_id"]) == product_id

    duplicate = authed_client.post(
        "/api/v1/barcodes/", {"product_id": product_id, "barcode": "6001234567890"}, format="json"
    )
    assert duplicate.status_code == 400
    assert duplicate.data["error"]["code"] == "validation_error"
