# Stockflow Database Design

* **Status:** Proposed
* **Version:** 0.1
* **Database:** PostgreSQL
* **Backend:** Django REST Framework
* **Architecture:** Modular monolith

## 1. Purpose

This document defines Stockflow's proposed relational schema, important constraints, indexes, and persistence rules.

It is a logical design, not a final migration specification. Field types, Django model definitions, and constraints should be validated during implementation.

## 2. General conventions

* Use UUID primary keys for durable entity identifiers.
* Keep human-readable business identifiers, such as SKUs and order numbers, in separate unique columns.
* Use timezone-aware timestamps and a consistent UTC storage convention.
* Use `DecimalField`/PostgreSQL `NUMERIC` for money and fractional quantities. Never use floating point for monetary values.
* Use explicit foreign keys and deliberate deletion policies.
* Archive entities referenced by historical transactions rather than hard-deleting them.
* Use database transactions for multi-record business operations.
* Enforce row-level invariants with database constraints wherever possible.
* Enforce cross-row invariants through transactional domain services, locking, and tests.
* Record request or correlation IDs where they help connect API requests, logs, and audit events.

## 3. Schema overview

The proposed tables are grouped by domain.

### 3.1 Company configuration and catalogue

#### `organizations`

Suggested fields:

* `id` — UUID primary key
* `name`
* `legal_name` — nullable
* `reporting_currency_code` — foreign key to `currencies`
* `created_at`
* `updated_at`

V1 represents one company. Keeping an organization record does not mean the application is already safe for multi-tenant operation.

#### `currencies`

* `code` — ISO 4217 currency code, primary key
* `name`
* `minor_unit_digits`
* `is_active`

#### `exchange_rates`

* `id` — UUID primary key
* `base_currency_code` — foreign key
* `quote_currency_code` — foreign key
* `rate` — `NUMERIC` with sufficient precision
* `effective_at`
* `source`
* `created_at`

Preserve the exchange-rate snapshot used for a transaction. Historical totals must not be recomputed using the latest rate.

#### `product_categories`

* `id` — UUID primary key
* `name`
* `parent_id` — nullable self-referencing foreign key
* `is_active`
* `created_at`
* `updated_at`

#### `products`

* `id` — UUID primary key
* `sku` — unique
* `name`
* `description`
* `category_id` — nullable foreign key
* `base_uom_code`
* `allows_fractional_quantity`
* `default_sales_price` — nullable `NUMERIC`
* `default_sales_currency_code` — nullable foreign key
* `is_active`
* `archived_at` — nullable
* `created_at`
* `updated_at`

SKU uniqueness is company-wide in v1. Avoid reusing archived SKUs if doing so could make historical documents or external references ambiguous.

#### `product_barcodes`

* `id` — UUID primary key
* `product_id` — foreign key
* `barcode` — unique
* `barcode_type` — nullable
* `created_at`

#### `warehouses`

* `id` — UUID primary key
* `code` — unique
* `name`
* `address` — nullable
* `is_active`
* `created_at`
* `updated_at`

#### `storage_locations`

* `id` — UUID primary key
* `warehouse_id` — foreign key
* `code`
* `name` — nullable
* `location_type`, such as `storage`, `receiving`, `quarantine`, or `dispatch`
* `is_active`
* Unique constraint on `(warehouse_id, code)`

Every location belongs to exactly one warehouse. If a warehouse-level default location is required, model it explicitly instead of using a nullable location to mean several different things.

#### `customers`

* `id` — UUID primary key
* `customer_code` — unique
* `name`
* Contact and delivery fields
* `is_active`
* `archived_at` — nullable
* `created_at`
* `updated_at`

#### `suppliers`

* `id` — UUID primary key
* `supplier_code` — unique
* `name`
* Contact fields
* `is_active`
* `archived_at` — nullable
* `created_at`
* `updated_at`

### 3.2 Inventory

#### `stock_balances`

Represents current quantity for a product/warehouse/location/status bucket.

Suggested fields:

* `id` — UUID primary key
* `product_id` — foreign key
* `warehouse_id` — foreign key
* `location_id` — foreign key
* `stock_status` — for example, `sellable`, `quarantine`, `damaged`, or `in_transit`
* `on_hand_qty` — `NUMERIC`
* `reserved_qty` — `NUMERIC`
* `version` — integer, optional concurrency aid
* `updated_at`

Constraints and rules:

* Unique `(product_id, warehouse_id, location_id, stock_status)`.
* `on_hand_qty >= 0`.
* `reserved_qty >= 0`.
* For reservable stock buckets, `reserved_qty <= on_hand_qty`.
* Reservations may target only eligible sellable stock.
* Non-sellable stock statuses are excluded from available-to-promise calculations.
* A location must belong to the same warehouse recorded on the balance.
* Use stable balance rows where practical so concurrent operations can lock them reliably.

For sellable stock:

`available_qty = on_hand_qty - reserved_qty`

Calculate availability from the authoritative quantities rather than maintaining a separately mutable `available_qty` field.

In-transit stock needs special care. It is operationally distinct from stock physically present at a warehouse. It may be represented through dedicated in-transit balances linked to a transfer or through explicit transfer-in-transit records. Choose one authoritative representation and prevent the same quantity from being counted in both.

#### `stock_movements`

Append-only records of physical stock changes.

Suggested fields:

* `id` — UUID primary key
* `product_id` — foreign key
* `warehouse_id` — foreign key
* `location_id` — foreign key
* `stock_status`
* `quantity_delta` — `NUMERIC`, non-zero
* `movement_type`
* `reference_type`
* `reference_id`, or a typed foreign key where practical
* `reason_code` — nullable
* `notes` — nullable
* `actor_user_id` — nullable foreign key
* `integration_client_id` — nullable foreign key
* `correlation_id` — nullable
* `occurred_at`
* `created_at`

Rules:

* Normal application roles must not update or delete posted movements.
* Corrections use new compensating movements.
* Every physical balance update and its movement record occur in the same transaction.
* Every movement must be traceable to a receipt, shipment, transfer, return, or adjustment.
* Use a unique source-operation key where possible to prevent duplicate posting.

Do not represent a reservation as a physical stock movement. Reservation activity changes availability, not physical on-hand quantity.

#### `stock_reservations`

* `id` — UUID primary key
* `order_line_id` — foreign key
* `warehouse_id` — foreign key
* `requested_qty`
* `allocated_qty`
* `consumed_qty`
* `released_qty`
* `status`
* `expires_at`
* `created_at`
* `updated_at`

Define and validate the quantity invariant. For example, consumed plus released quantity must never exceed allocated quantity.

Requested quantity may exceed allocated quantity when the order is backordered. Decide whether a reservation record represents the overall request or an individual reservation attempt; keep that meaning consistent.

#### `reservation_allocations`

* `id` — UUID primary key
* `reservation_id` — foreign key
* `stock_balance_id` — foreign key
* `allocated_qty`
* `consumed_qty`
* `released_qty`
* `created_at`
* `updated_at`

One reservation may allocate from multiple locations. Each allocation identifies the stock bucket that was committed.

The sum of active allocations must match the active allocated quantity on the reservation. This is a cross-row invariant, so validate it transactionally and with domain tests.

#### `reservation_events`

Recommended append-only reservation history.

* `id` — UUID primary key
* `reservation_id` — foreign key
* `event_type`, such as `created`, `allocated`, `consumed`, `released`, `expired`, or `cancelled`
* `quantity`
* `actor_user_id` — nullable foreign key
* `reason` — nullable
* `created_at`
* `correlation_id` — nullable

This records reservation lifecycle changes separately from the physical stock movement ledger.

#### `inventory_adjustments`

* `id` — UUID primary key
* `adjustment_number` — unique
* `status`, such as `draft`, `approved`, `posted`, or `cancelled`
* `warehouse_id` — foreign key
* `reason_code`
* `created_by` — foreign key
* `approved_by` — nullable foreign key
* `posted_at` — nullable
* `created_at`
* `updated_at`

#### `inventory_adjustment_lines`

* `id` — UUID primary key
* `adjustment_id` — foreign key
* `product_id` — foreign key
* `location_id` — foreign key
* `stock_status`
* `expected_qty` — nullable
* `counted_qty` — nullable
* `quantity_delta`
* `notes` — nullable

Posting an adjustment creates stock movements and updates balances atomically. Require approval for configured adjustment types or thresholds.

### 3.3 Sales and fulfilment

#### `orders`

* `id` — UUID primary key
* `order_number` — unique
* `customer_id` — foreign key
* `warehouse_id` — foreign key identifying the selected warehouse
* `source`, such as `staff` or `external_api`
* `status`
* `currency_code` — foreign key
* `created_by_user_id` — nullable foreign key
* `integration_client_id` — nullable foreign key
* `external_reference` — nullable
* `submitted_at` — nullable
* `created_at`
* `updated_at`

Set the creator from the authenticated identity. External callers must not be able to nominate arbitrary internal user IDs.

#### `order_lines`

* `id` — UUID primary key
* `order_id` — foreign key
* `product_id` — foreign key
* `ordered_qty`
* `cancelled_qty`, default `0`
* `fulfilled_qty`, default `0`
* `unit_price` — `NUMERIC`
* `currency_code` — foreign key or inherited from the order under an enforced rule
* `created_at`
* `updated_at`

The unit price is a snapshot. Add discounts and tax fields only when their business rules are defined; v1 is not a full accounting or tax engine.

#### `pick_lists`

* `id` — UUID primary key
* `pick_list_number` — unique
* `order_id` — foreign key
* `warehouse_id` — foreign key
* `status`
* `assigned_to_user_id` — nullable foreign key
* `created_at`
* `updated_at`

#### `pick_list_lines`

* `id` — UUID primary key
* `pick_list_id` — foreign key
* `order_line_id` — foreign key
* `stock_balance_id` — foreign key
* `planned_qty`
* `picked_qty`
* `created_at`
* `updated_at`

Picking is not dispatch. Pick confirmation must not reduce physical stock under Stockflow's default policy.

#### `shipments`

* `id` — UUID primary key
* `shipment_number` — unique
* `order_id` — foreign key
* `status`
* `dispatched_at` — nullable
* `delivered_at` — nullable
* `carrier_reference` — nullable
* `created_at`
* `updated_at`

#### `shipment_lines`

* `id` — UUID primary key
* `shipment_id` — foreign key
* `order_line_id` — foreign key
* `quantity`
* `created_at`

Shipment posting updates fulfilled quantities and stock balances/movements in a single transaction. Cumulative shipped quantity must not exceed the permitted order quantity after cancellation rules are applied.

### 3.4 Procurement

#### `purchase_orders`

* `id` — UUID primary key
* `po_number` — unique
* `supplier_id` — foreign key
* `warehouse_id` — foreign key
* `status`
* `currency_code` — foreign key
* `created_by_user_id` — foreign key
* `ordered_at` — nullable
* `created_at`
* `updated_at`

#### `purchase_order_lines`

* `id` — UUID primary key
* `purchase_order_id` — foreign key
* `product_id` — foreign key
* `ordered_qty`
* `received_accepted_qty`, if maintained as a transactional projection
* `cancelled_qty`
* `unit_cost` — `NUMERIC`
* `created_at`
* `updated_at`

If received totals are stored for performance, update them transactionally and test them against the receipt-line totals.

#### `goods_receipts`

* `id` — UUID primary key
* `receipt_number` — unique
* `purchase_order_id` — foreign key
* `warehouse_id` — foreign key
* `status`
* `received_by_user_id` — foreign key
* `idempotency_record_id` — nullable foreign key
* `received_at`
* `created_at`

#### `goods_receipt_lines`

* `id` — UUID primary key
* `goods_receipt_id` — foreign key
* `purchase_order_line_id` — foreign key
* `accepted_qty`
* `damaged_qty`
* `rejected_qty`
* `destination_location_id` — foreign key
* `notes` — nullable

Validate non-negative quantities and outstanding purchase-order quantities. Over-receipt is rejected unless an authorized policy permits it.

Accepted, damaged, and rejected quantities must remain distinguishable.

#### `supplier_returns` and `supplier_return_lines`

Track supplier returns and post the corresponding stock reduction when the return is dispatched or otherwise committed. Link to the original receipt when available.

### 3.5 Transfers

#### `transfers`

* `id` — UUID primary key
* `transfer_number` — unique
* `source_warehouse_id` — foreign key
* `destination_warehouse_id` — foreign key
* `status`
* `requested_by_user_id` — foreign key
* `approved_by_user_id` — nullable foreign key
* `dispatched_at` — nullable
* `received_at` — nullable
* `created_at`
* `updated_at`

Source and destination warehouses must differ.

#### `transfer_lines`

* `id` — UUID primary key
* `transfer_id` — foreign key
* `product_id` — foreign key
* `requested_qty`
* `dispatched_qty`
* `received_accepted_qty`
* `received_damaged_qty`
* `received_missing_qty`

#### `transfer_dispatches`, `transfer_dispatch_lines`, `transfer_receipts`, and `transfer_receipt_lines`

Use explicit dispatch and receipt records if a transfer can be split across multiple dispatches or deliveries.

Link each line to the relevant source or destination location. At dispatch, reduce source stock and record in-transit quantity. At receipt, reduce in-transit quantity and add accepted or damaged quantities to the destination's appropriate stock bucket.

Do not create destination sellable stock at dispatch.

### 3.6 Identity, integrations, idempotency, audit, and outbox

#### `users`, `roles`, `permissions`, and `user_roles`

Standard identity and role-based access records. Use unique role and permission codes.

If a role assignment is scoped to a warehouse, model that scope explicitly.

#### `user_warehouse_access`

* `id` — UUID primary key
* `user_id` — foreign key
* `warehouse_id` — foreign key
* `access_level` or permission relationship

Add uniqueness constraints appropriate to the chosen permission model.

#### `integration_clients`

* `id` — UUID primary key
* `name`
* `credential_hash`
* `is_active`
* `created_at`
* `last_used_at` — nullable

Store hashes of API secrets, not raw secrets. Support credential rotation, revocation, and narrowly scoped permissions.

#### `integration_permissions`

Links integration clients to permitted actions and scopes. Do not grant broad access by default.

#### `idempotency_records`

* `id` — UUID primary key
* `client_scope`, representing the authenticated user or integration client
* `idempotency_key`
* `request_hash`
* `response_status`
* `response_body` or stable result reference
* `created_at`
* `expires_at`, according to retention policy

Enforce uniqueness on `(client_scope, idempotency_key)`.

If a key is reused with a different request hash, reject the request. Coordinate idempotency handling and the business operation transactionally so concurrent duplicate requests cannot both perform the operation.

#### `audit_events`

* `id` — UUID primary key
* `actor_type` and `actor_id`, or typed actor references
* `action`
* `resource_type` and `resource_id`
* `occurred_at`
* `correlation_id`
* `before_data` and `after_data` as JSONB where justified
* `reason` — nullable

Avoid storing secrets or unnecessary personal data in snapshots. Restrict update and delete access.

#### `outbox_events`

* `id` — UUID primary key
* `event_type`
* `aggregate_type` and `aggregate_id`
* `payload` — JSONB
* `created_at`
* `published_at` — nullable
* `attempt_count`
* `next_attempt_at` — nullable
* `last_error` — nullable

Insert the outbox event in the same transaction as the business change. A background publisher sends events and records publication attempts.

Delivery is at-least-once; consumers must tolerate duplicate events.

## 4. Important constraints and indexes

At minimum, consider:

* Unique product SKUs and barcodes
* Unique warehouse codes and location codes within each warehouse
* Unique customer and supplier codes
* Unique order, purchase order, receipt, shipment, transfer, and adjustment numbers
* Unique stock balance tuple `(product, warehouse, location, status)`
* Non-negative stock quantities and relevant transaction-line quantities
* `reserved_qty <= on_hand_qty` for reservable buckets
* Active reservations indexed by status and expiry time
* Order lines indexed by order and product
* Purchase orders and receipts indexed by supplier, warehouse, and status
* Transfers indexed by source warehouse, destination warehouse, and status
* Idempotency uniqueness on `(client_scope, idempotency_key)`
* Audit events indexed by `(resource_type, resource_id, occurred_at)`
* Unpublished outbox events indexed by publication state and retry time

Use partial indexes for active reservations or unpublished outbox events when query patterns justify them.

Validate indexes against realistic data and query plans. Avoid indexing every field without evidence that it improves performance.

## 5. Transaction boundaries

### 5.1 Reserve order stock

Within one database transaction:

1. Lock the order line and relevant stock balances, or use atomic conditional updates.
2. Calculate eligible available quantity from current state.
3. Allocate available quantity according to policy.
4. Create or update reservation and allocation records.
5. Increase each affected balance's reserved quantity.
6. Append reservation events and audit/outbox events.
7. Commit.

If stock is insufficient and backorders are allowed, reserve only available quantity and leave the remainder backordered. Never reserve more than available stock.

### 5.2 Expire reservation

Within one transaction:

1. Find expired active reservations using the database clock.
2. Lock the reservation and allocation rows.
3. Release only the remaining active allocations.
4. Decrease reserved quantities by exactly the released amount.
5. Record expiration events.
6. Commit.

The process must remain safe if multiple workers attempt to expire the same reservation. Expiry does not cancel the sales order.

### 5.3 Receive goods

Within one transaction:

1. Validate the receipt and idempotency key.
2. Lock the purchase order and relevant lines.
3. Validate outstanding quantities and over-receipt policy.
4. Create receipt and receipt-line records.
5. Update stock balances and append movements for accepted and damaged quantities.
6. Update purchase-order receipt state.
7. Write audit/outbox events and the idempotency result.
8. Commit.

### 5.4 Dispatch shipment

Within one transaction:

1. Validate shipment state and idempotency key.
2. Lock the shipment, order lines, allocations, and balances as required.
3. Verify that dispatch quantity is authorized and reserved stock can be consumed.
4. Decrease on-hand quantity and the corresponding reserved quantity.
5. Append stock movements and update shipment/order fulfilment records.
6. Write audit/outbox events and the idempotency result.
7. Commit.

Define how undispatched reservations are retained or released. Never deduct the same shipment twice.

### 5.5 Dispatch and receive transfer

**Dispatch transaction:**

* Validate the approved transfer and available source stock.
* Reduce source on-hand quantity.
* Add dispatched quantity to an explicit in-transit representation.
* Create the dispatch record and associated movements.
* Commit the transfer dispatch state.

**Receipt transaction:**

* Validate the unreceived in-transit quantity.
* Reduce the in-transit quantity.
* Add accepted quantity to destination sellable stock.
* Add damaged quantity to a non-sellable bucket.
* Record missing or short quantities and resolve the in-transit balance consistently.
* Mark the receipt posted.

## 6. Concurrency and correctness

* Use Django `transaction.atomic()` for each business command.
* Use `select_for_update()` or conditional SQL updates to serialize competing stock operations.
* Acquire locks in a consistent order, such as sorted balance IDs, to reduce deadlocks.
* Retry only known transient transaction failures, using a bounded retry policy.
* Never treat a previous availability read as authoritative; revalidate under lock at commit time.
* Use database uniqueness constraints as the final protection against duplicate keys.
* Keep external network calls outside database transactions.
* Use the outbox pattern for downstream notifications and events.

Required concurrency tests include two orders competing for the last available units, concurrent reservation expiry, duplicate receipt submission, duplicate shipment dispatch, and transfer receipt retries.

## 7. Data retention and deletion

* Archive products, customers, suppliers, warehouses, and users when historical references exist.
* Preserve posted stock movements and posted transaction records.
* Define retention periods for audit events, idempotency records, application logs, and failed outbox events before production.
* Never cascade-delete ledger history when a catalogue record is archived.
* Document and periodically test database backup and restoration procedures.

## 8. Implementation notes

Translate this logical model into Django models and migrations in small, reviewable increments.

Prefer explicit domain services for stock operations. Model signals must not be the primary mechanism for business-critical inventory changes because they can obscure transaction boundaries and failure behavior.

Before release, implement:

* Database constraints where possible
* Domain validation for cross-row invariants
* Concurrency and retry tests
* Migration tests
* Balance and reservation reconciliation
* Documented backup and restore procedures
