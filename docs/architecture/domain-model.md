# Stockflow Domain Model

* **Status:** Proposed
* **Version:** 0.1
* **Product:** Stockflow — Inventory & Fulfilment Platform

## 1. Purpose

This document defines Stockflow's core business concepts, their responsibilities, and the rules governing how they interact. It serves as the domain-level reference for backend modules, API design, database design, and testing.

Stockflow targets wholesale and distribution businesses operating multiple warehouses. Orders may be created by staff or submitted through external integrations.

## 2. Scope

### In scope

* Product catalogue and SKU management
* Multiple warehouses and optional storage locations
* Inventory balances and stock movement ledger
* Reservations, allocation, and backorders
* Customers and suppliers
* Purchase orders and goods receiving
* Sales orders, picking, packing, dispatch, and delivery tracking
* Inter-warehouse transfers
* Returns and inventory adjustments
* Role-based access control and audit trails
* Reporting, alerts, and external API access
* Multiple transaction currencies

### Out of scope for the initial release

* General ledger and full accounting
* Payroll and human resources
* Manufacturing resource planning
* Fleet management and route optimization
* Marketplace functionality
* Native mobile applications
* AI-driven demand forecasting

## 3. Architectural principles

1. **Modular monolith first.** Modules are separated by responsibility but deployed as one application.
2. **Inventory owns stock changes.** Other modules request stock operations through inventory application services. They must never update stock balances directly.
3. **Ledger plus balance projection.** The stock movement ledger records physical stock changes, while stock balances represent current state.
4. **Atomic business operations.** Related business records, balance updates, movements, and applicable audit/outbox events commit together.
5. **Preserved history.** Posted stock movements are immutable. Errors are corrected through compensating movements.
6. **Idempotent operations.** Retried requests must not duplicate receipts, reservations, dispatches, or transfers.
7. **Server-side authorization.** Frontend visibility is not an authorization boundary.
8. **Explicit state transitions.** Orders, reservations, purchase orders, shipments, and transfers use validated transitions.
9. **Exact monetary values.** Money uses decimal database types, never binary floating point.
10. **Explicit currency conversion.** Values in different currencies must not be aggregated without a defined conversion policy.

## 4. Core domain concepts

### 4.1 Organization

The initial deployment represents one company with multiple warehouses.

An organization record may hold company-level configuration, including company details and reporting currency. However, version one does not require cross-company tenant isolation.

### 4.2 Product

A product represents an item the company buys, stores, or sells.

Important attributes include:

* SKU, unique within the company
* Name and description
* Category
* Base unit of measure
* Optional barcode identifiers
* Active or archived state
* Optional default sales price and purchasing reference cost

Products referenced by historical transactions must be archived rather than hard-deleted.

**Unit policy:** Each product has one base unit of measure. Fractional quantities are permitted only for products explicitly configured to support them. Unit conversion must not happen implicitly.

### 4.3 Warehouse and storage location

A warehouse represents a physical or operational stock-holding site.

A storage location represents an optional subdivision within a warehouse, such as a bin, shelf, receiving area, quarantine area, or dispatch area.

Every storage location belongs to exactly one warehouse. A warehouse may use a designated default location when bin-level tracking is unnecessary.

### 4.4 Stock balance

A stock balance represents the current quantity of a product at a specific warehouse, location, and stock-status bucket.

* **On-hand quantity:** Physical quantity recorded in that bucket.
* **Reserved quantity:** Sellable on-hand quantity committed to active reservations.
* **Available quantity:** Sellable on-hand quantity minus active reserved quantity.
* **Backordered quantity:** Demand that has not yet been allocated. It is not inventory and is not reserved.
* **In-transit quantity:** Quantity dispatched from one warehouse but not yet accepted at its destination.

Damaged and quarantined quantities are not sellable. They must be represented through explicit stock statuses or an equivalent model that excludes them from availability calculations.

### 4.5 Stock movement

A stock movement is an immutable record of a physical stock change.

Examples include:

* Receiving accepted goods
* Moving goods into damaged or quarantine stock
* Dispatching an order
* Dispatching or receiving a warehouse transfer
* Accepting a customer return into a stock bucket
* Dispatching a supplier return
* Posting an authorized inventory adjustment
* Correcting an earlier movement through a compensating movement

Each movement records the product, affected stock bucket, signed quantity change, movement type, source reference, timestamp, and applicable actor or system identity.

**Important distinction:** A reservation changes availability, not physical on-hand quantity. Reservation creation and release should be recorded in reservation events or a dedicated reservation ledger rather than being misrepresented as physical stock movements.

### 4.6 Reservation and allocation

A reservation commits available stock to an order line for a limited period.

* A reservation may be partially allocated.
* An allocation identifies the specific stock balance and quantity committed.
* A reservation may draw from multiple locations when permitted by the allocation policy.
* The default reservation expiry is 24 hours after creation.
* Expiry releases only quantities that remain actively reserved.
* Expiry does not automatically cancel the order.
* A reservation may be consumed, released, expired, or cancelled.

A backorder represents the portion of an order line that has not been allocated. It is demand awaiting stock, not reserved inventory.

### 4.7 Customer and supplier

Customers place sales orders. Suppliers provide products and receive purchase orders.

Customer and supplier records referenced by historical transactions must be archived rather than deleted.

### 4.8 Purchase order and goods receipt

A purchase order records intended purchases from a supplier. It may be received in multiple deliveries.

A goods receipt records the quantities physically received and classifies them as:

* Accepted
* Damaged or quarantined
* Rejected

Only accepted quantities enter sellable stock. Damaged quantities enter a non-sellable stock bucket. Rejected goods do not enter stock unless a controlled quarantine workflow explicitly records them.

Over-receipt is rejected by default unless an authorized policy permits it.

Receipt submission must be idempotent. Replaying the same receipt request must not add stock twice.

### 4.9 Sales order and order line

An order records customer demand and its source, either staff-created or externally submitted. The authenticated staff member or integration identity is recorded as the creator.

Each order line records the product, ordered quantity, price, currency, fulfilled quantity, cancelled quantity, and allocation information.

Prices and currencies are snapshotted when the order is submitted. Subsequent catalogue price changes must not alter historical orders.

For each order line:

`outstanding_qty = ordered_qty - cancelled_qty - fulfilled_qty`

`backordered_qty = max(0, ordered_qty - cancelled_qty - fulfilled_qty - active_allocated_qty)`

Allocated-but-unfulfilled quantity remains operationally outstanding, but it is not backordered.

These quantities may be derived from authoritative records or maintained as transactional projections. Avoid independently mutable duplicate quantities unless there is a demonstrated performance need and reconciliation tests protect their correctness.

### 4.10 Picking, shipment, and delivery

Picking identifies quantities collected from stock. Packing prepares them for dispatch. A shipment records dispatched quantities and subsequent delivery updates.

Dispatch must not exceed the quantity authorized for fulfilment.

The default physical stock deduction point is dispatch confirmation, not pick-list creation. Dispatching the same shipment twice must not deduct stock twice.

Order state and shipment state are separate. A sales order may be fulfilled through multiple partial shipments.

### 4.11 Inter-warehouse transfer

A transfer moves stock from a source warehouse to a destination warehouse.

Suggested lifecycle:

1. Requested or drafted
2. Approved
3. Source stock allocated
4. Dispatched
5. Partially or fully received at destination
6. Closed after discrepancies are resolved or recorded

At dispatch, source stock decreases and the dispatched quantity becomes in transit. At destination receipt, accepted quantity enters destination stock.

The destination must not show transferred goods as available before receipt. Shortages, damage, and missing quantities must be recorded explicitly.

### 4.12 Returns and adjustments

Customer returns require inspection before their stock disposition is decided. Returned goods may enter sellable, damaged, or quarantine stock.

A return does not automatically imply a refund; financial settlement is outside the initial inventory scope.

Inventory adjustments require an authorized reason and actor. Corrections must preserve the original history through compensating movements.

### 4.13 Identity, integrations, and audit

Users receive roles and permissions. Warehouse-scoped permissions limit which warehouses and locations a user can operate on.

External integrations use separate credentials and explicit permissions.

Audit events record the actor, action, timestamp, affected resource, correlation identifier, and relevant change details. Credentials, tokens, and other secrets must never be copied into audit payloads.

## 5. Module ownership

| Module              | Owns                                           | Must not do                                     |
| ------------------- | ---------------------------------------------- | ----------------------------------------------- |
| Catalogue           | Products, categories, barcodes                 | Change stock directly                           |
| Warehousing         | Warehouses, locations, warehouse access        | Bypass inventory operations                     |
| Inventory           | Balances, movements, reservations, adjustments | Own sales or purchasing workflows               |
| Procurement         | Purchase orders, receipts, supplier returns    | Directly edit balances                          |
| Sales               | Orders, order lines, customer order lifecycle  | Directly reserve or deduct stock                |
| Fulfilment          | Pick lists, packing, shipments                 | Deduct stock outside inventory services         |
| Transfers           | Transfer workflow and receipts                 | Make destination stock available before receipt |
| Identity and access | Users, roles, permissions, integration clients | Trust client-side authorization                 |
| Audit and reporting | Audit events and read models                   | Mutate historical transactions                  |

Modules may call each other's application services through explicit interfaces. Avoid circular dependencies and hidden business operations in model signals.

## 6. State machines

Use explicit transition functions rather than arbitrary status updates.

### Sales order

Suggested states:

* `draft`
* `submitted`
* `confirmed`
* `in_fulfilment`
* `partially_fulfilled`
* `fulfilled`
* `cancelled`
* `rejected`

A backordered order may remain confirmed or partially fulfilled while waiting for stock. Avoid a single `backordered` order status when an order can contain allocated, backordered, and fulfilled quantities simultaneously.

### Reservation

* `active`
* `partially_consumed`
* `consumed`
* `released`
* `expired`
* `cancelled`

Transitions must be transactional and idempotent.

### Purchase order

* `draft`
* `submitted`
* `partially_received`
* `received`
* `cancelled`
* `closed`

### Shipment

* `draft`
* `ready`
* `dispatched`
* `partially_delivered`
* `delivered`
* `cancelled`

A dispatched shipment must not be cancelled as though the goods never left the warehouse. Use a return or explicit reversal workflow instead.

### Transfer

* `draft`
* `approved`
* `dispatched`
* `partially_received`
* `received`
* `closed`
* `cancelled`

A transfer may be cancelled only before dispatch. After dispatch, use a controlled resolution or reversal process.

Exact transition rules must be implemented and tested in domain services.

## 7. Backorder allocation policy

Recommended initial policy:

1. Allocate newly available stock to the oldest eligible backorder first, using creation time and a stable identifier as tie-breakers.
2. Allocate only from the warehouse selected for the order.
3. Perform allocation transactionally using the same locking or conditional-update strategy as normal reservations.
4. Exclude cancelled and already fulfilled quantities.
5. Require an explicit permission and audit reason for any staff override of priority.
6. Never silently change an order's selected warehouse to satisfy a backorder.

Whether allocation is fully automatic or requires staff approval remains a product decision. Encapsulate the policy so it can change without rewriting the inventory ledger.

## 8. Currency and pricing

* Support multiple ISO currency codes on sales and purchase documents.
* Store original currency and exact decimal amounts.
* Snapshot prices at order submission.
* Make the company's reporting currency configurable.
* Store any applied exchange-rate snapshot with its source and effective timestamp.
* Never aggregate amounts across currencies without explicit conversion.
* Exclude inventory valuation and accounting-grade foreign-exchange gain/loss treatment from v1.

## 9. Critical invariants

1. Sellable on-hand quantity must never become negative.
2. Reserved quantity must never be negative or exceed eligible on-hand quantity.
3. Every physical stock change must have a traceable movement and source reference.
4. Retried commands must not duplicate receipts, reservations, dispatches, or transfer effects.
5. Every movement must identify its product and stock location or bucket.
6. Posted movements are immutable; corrections use compensating events.
7. Only valid state transitions are accepted.
8. All permissions are enforced server-side.
9. Related business records, balance changes, movements, and outbox records commit atomically.
10. In-transit stock is not available at the destination before receipt.
11. Damaged and quarantined stock is not sellable.
12. Quantities and money use appropriate exact data types and validated precision.

## 10. Open decisions before production

* Whether backorder allocation is fully automatic or staff-confirmed
* Whether reservations can be renewed and under what limits
* Whether stock can be allocated across multiple locations within a warehouse
* Whether over-receipt is permitted and who may authorize it
* Company reporting currency and exchange-rate source
* Audit and transaction retention periods
* Notification channels and retry policies
* Detailed treatment of taxes and discounts, if required
