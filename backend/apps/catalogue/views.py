"""Catalogue endpoints. Reads, creates, and updates only; nothing here deletes."""

from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, viewsets

from common.permissions import ActiveUserPermission

from .models import (
    Customer,
    Product,
    ProductBarcode,
    ProductCategory,
    StorageLocation,
    Supplier,
    Warehouse,
)
from .serializers import (
    CustomerSerializer,
    ProductBarcodeSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    StorageLocationSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)


class CatalogueViewSet(viewsets.ModelViewSet):
    permission_classes = [ActiveUserPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]


class ProductCategoryViewSet(CatalogueViewSet):
    queryset = ProductCategory.objects.select_related("parent").all()
    serializer_class = ProductCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class ProductViewSet(CatalogueViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["sku", "name", "description"]
    ordering_fields = ["sku", "name", "created_at"]
    ordering = ["sku"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if params.get("is_active") is not None:
            queryset = queryset.filter(is_active=params["is_active"].lower() == "true")
        if params.get("category_id"):
            queryset = queryset.filter(category_id=params["category_id"])
        return queryset


class ProductBarcodeViewSet(CatalogueViewSet):
    queryset = ProductBarcode.objects.select_related("product").all()
    serializer_class = ProductBarcodeSerializer
    lookup_field = "barcode"

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class WarehouseViewSet(CatalogueViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name", "created_at"]
    ordering = ["code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset


class WarehouseLocationListCreateView(generics.ListCreateAPIView):
    permission_classes = [ActiveUserPermission]
    serializer_class = StorageLocationSerializer

    def get_warehouse(self):
        return get_object_or_404(Warehouse, pk=self.kwargs["warehouse_pk"])

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]
            data = data.copy() if hasattr(data, "copy") else dict(data)
            data["warehouse_id"] = str(self.get_warehouse().pk)
            kwargs["data"] = data
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        return StorageLocation.objects.filter(warehouse=self.get_warehouse()).order_by("code")

    def perform_create(self, serializer):
        serializer.save(warehouse=self.get_warehouse())


class StorageLocationViewSet(CatalogueViewSet):
    queryset = StorageLocation.objects.select_related("warehouse").all()
    serializer_class = StorageLocationSerializer


class CustomerViewSet(CatalogueViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["customer_code", "name", "email"]
    ordering_fields = ["customer_code", "name", "created_at"]
    ordering = ["customer_code"]


class SupplierViewSet(CatalogueViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["supplier_code", "name", "email"]
    ordering_fields = ["supplier_code", "name", "created_at"]
    ordering = ["supplier_code"]
