"""Catalogue serializers. Field names follow docs/architecture/api-specification.md."""

from rest_framework import serializers

from .models import (
    Customer,
    Product,
    ProductBarcode,
    ProductCategory,
    StorageLocation,
    Supplier,
    Warehouse,
)


class ProductCategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent", queryset=ProductCategory.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "parent_id", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if parent is not None and self.instance is not None and parent.pk == self.instance.pk:
            raise serializers.ValidationError({"parent_id": "A category cannot be its own parent."})
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=ProductCategory.objects.all(), allow_null=True, required=False
    )
    base_unit = serializers.CharField(source="base_uom")

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "category_id",
            "base_unit",
            "allows_fractional_quantity",
            "default_sales_price",
            "default_sales_currency",
            "is_active",
            "archived_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "archived_at", "created_at", "updated_at"]


class ProductBarcodeSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=Product.objects.all()
    )

    class Meta:
        model = ProductBarcode
        fields = ["id", "product_id", "barcode", "barcode_type", "created_at"]
        read_only_fields = ["id", "created_at"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name", "address", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StorageLocationSerializer(serializers.ModelSerializer):
    warehouse_id = serializers.PrimaryKeyRelatedField(
        source="warehouse", queryset=Warehouse.objects.all()
    )

    class Meta:
        model = StorageLocation
        fields = [
            "id",
            "warehouse_id",
            "code",
            "name",
            "location_type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "customer_code",
            "name",
            "email",
            "phone",
            "address",
            "is_active",
            "archived_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "archived_at", "created_at", "updated_at"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "supplier_code",
            "name",
            "email",
            "phone",
            "is_active",
            "archived_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "archived_at", "created_at", "updated_at"]
