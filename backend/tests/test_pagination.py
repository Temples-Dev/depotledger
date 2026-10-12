"""Tests for the standard paginated collection envelope."""

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from common.pagination import StandardResultsPagination


def paginate(count, query=""):
    factory = APIRequestFactory()
    request = Request(factory.get(f"/api/v1/example/{query}"))
    paginator = StandardResultsPagination()
    items = [{"id": index} for index in range(count)]
    page = paginator.paginate_queryset(items, request)
    return paginator, paginator.get_paginated_response(page).data


def test_default_page_size_is_25():
    paginator, body = paginate(30)
    assert paginator.page_size == 25
    assert body["count"] == 30
    assert len(body["results"]) == 25
    assert body["next"] is not None
    assert body["previous"] is None


def test_page_size_param_is_capped_at_100():
    paginator, body = paginate(150, "?page_size=200")
    assert len(body["results"]) == 100


def test_explicit_page_size_is_honoured_within_cap():
    _, body = paginate(30, "?page_size=10")
    assert len(body["results"]) == 10


def test_collection_envelope_keys():
    _, body = paginate(3)
    assert set(body) == {"count", "next", "previous", "results"}
