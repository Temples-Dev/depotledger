"""Catalogue master data.

Covers categories, products, barcodes, warehouses, locations, customers, and
suppliers. Archive instead of delete: records referenced by historical
transactions are deactivated, never hard-deleted. There are no DELETE
endpoints for them.
"""

import uuid

from django.db import models
from django.utils import timezone


class ArchivableModel(models.Model):
    """Sets archived_at when a record is deactivated."""

    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.is_active and self.archived_at is None:
            self.archived_at = timezone.now()
        super().save(*args, **kwargs)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProductCategory(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(ArchivableModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        ProductCategory,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )
    base_uom = models.CharField(max_length=32)
    allows_fractional_quantity = models.BooleanField(default=False)
    default_sales_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    default_sales_currency = models.CharField(max_length=3, null=True, blank=True)

    def __str__(self):
        return f"{self.sku} — {self.name}"


class ProductBarcode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="barcodes")
    barcode = models.CharField(max_length=100, unique=True, db_index=True)
    barcode_type = models.CharField(max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.barcode


class Warehouse(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} — {self.name}"


class StorageLocation(models.Model):
    STORAGE = "storage"
    RECEIVING = "receiving"
    QUARANTINE = "quarantine"
    DISPATCH = "dispatch"
    LOCATION_TYPES = [
        (STORAGE, "Storage"),
        (RECEIVING, "Receiving"),
        (QUARANTINE, "Quarantine"),
        (DISPATCH, "Dispatch"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255, null=True, blank=True)
    location_type = models.CharField(max_length=32, choices=LOCATION_TYPES, default=STORAGE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"], name="unique_location_code_per_warehouse"
            )
        ]

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"


class Customer(ArchivableModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=64, blank=True, default="")
    address = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.customer_code} — {self.name}"


class Supplier(ArchivableModel, TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return f"{self.supplier_code} — {self.name}"
