"""Catalogue admin: master data maintenance screens."""

from django.contrib import admin

from .models import (
    Customer,
    Product,
    ProductBarcode,
    ProductCategory,
    StorageLocation,
    Supplier,
    Warehouse,
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "base_uom", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("sku", "name")


@admin.register(ProductBarcode)
class ProductBarcodeAdmin(admin.ModelAdmin):
    list_display = ("barcode", "product", "barcode_type")
    search_fields = ("barcode",)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("code", "warehouse", "location_type", "is_active")
    list_filter = ("location_type", "is_active", "warehouse")
    search_fields = ("code", "name")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("customer_code", "name")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("supplier_code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("supplier_code", "name")
