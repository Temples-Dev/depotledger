"""Catalogue routes, mounted under api/v1/."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    ProductBarcodeViewSet,
    ProductCategoryViewSet,
    ProductViewSet,
    StorageLocationViewSet,
    SupplierViewSet,
    WarehouseLocationListCreateView,
    WarehouseViewSet,
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", ProductCategoryViewSet, basename="category")
router.register("barcodes", ProductBarcodeViewSet, basename="barcode")
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("locations", StorageLocationViewSet, basename="location")
router.register("customers", CustomerViewSet, basename="customer")
router.register("suppliers", SupplierViewSet, basename="supplier")

urlpatterns = [
    path(
        "warehouses/<uuid:warehouse_pk>/locations/",
        WarehouseLocationListCreateView.as_view(),
        name="warehouse-locations",
    ),
    *router.urls,
]
