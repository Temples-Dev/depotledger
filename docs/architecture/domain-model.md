# depotledger — Domain Model

* **Status:** Approved
* **Version:** 1.0
* **Product:** depotledger — Inventory and Fulfilment Platform

## 1. Purpose

This document defines depotledger's core business concepts, their responsibilities, and the rules governing how they interact. It serves as the domain-level reference for backend modules, API design, database design, and testing.

depotledger targets wholesale and distribution businesses operating multiple warehouses. Orders may be created by staff or submitted through external integrations.

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

Store company-level configuration, including company details and reporting currency, in the organization record. Exclude cross-company tenant isolation from version one.

### 4.2 Product

Define a product as an item the company buys, stores, or sells.

Include the following attributes:

* SKU, unique within the company
* Name and description
* Category
* Base unit of measure
* Optional barcode identifiers
* Active or archived state
* Optional default sales price and purchasing reference cost

Archive products referenced by historical transactions. Never hard-delete them.

**Unit policy:** Give each product one base unit of measure. Permit fractional quantities only for explicitly configured products. Never convert units implicitly.

### 4.3 Warehouse and storage location

Define a warehouse as a physical or operational stock-holding site.

Define a storage location as a subdivision within a warehouse: bin, shelf, receiving area, quarantine area, or dispatch area.

Every storage location belongs to exactly one warehouse. Designate a default location for warehouses that skip bin-level tracking.

### 4.4 Stock balance

Record the current quantity of a product at a warehouse, location, and stock-status bucket in a stock balance.

* **On-hand quantity:** Physical quantity recorded in that bucket.
* **Reserved quantity:** Sellable on-hand quantity committed to active reservations.
* **Available quantity:** Sellable on-hand quantity minus active reserved quantity.
* **Backordered quantity:** Demand that has not yet been allocated. It is not inventory and is not reserved.
* **In-transit quantity:** Quantity dispatched from one warehouse but not yet accepted at its destination.

Exclude damaged and quarantined quantities from sellable stock. Represent them through explicit stock statuses that remove them from availability calculations.

### 4.5 Stock movement

Append a stock movement as the immutable record of every physical stock change.

Examples include:

* Receiving accepted goods
* Moving goods into damaged or quarantine stock
* Dispatching an order
* Dispatching or receiving a warehouse transfer
* Accepting a customer return into a stock bucket
* Dispatching a supplier return
* Posting an authorized inventory adjustment
* Correcting an earlier movement through a compensating movement

Record product, affected stock bucket, signed quantity change, movement type, source reference, timestamp, and actor or system identity in every movement.

**Important distinction:** A reservation changes availability, never physical on-hand quantity. Record reservation creation and release in reservation events or the reservation ledger. Never misrepresent them as physical stock movements.

### 4.6 Reservation and allocation

Commit available stock to an order line through a reservation. Enforce the reservation lifecycle below.

* Allocate a reservation partially where the policy permits.
* An allocation identifies the specific stock balance and quantity committed.
* Draw a reservation from multiple locations only where the allocation policy permits.
* Expire reservations 24 hours after creation by default.
* Release only actively reserved quantities on expiry.
* Keep the order open on reservation expiry.
* Close a reservation only through consume, release, expiry, or cancel transitions.

A backorder represents the portion of an order line that has not been allocated. It is demand awaiting stock, not reserved inventory.

### 4.7 Customer and supplier

Customers place sales orders. Suppliers provide products and receive purchase orders.

Archive customer and supplier records referenced by historical transactions. Never delete them.

### 4.8 Purchase order and goods receipt

Record intended supplier purchases in a purchase order. Receive it across multiple deliveries where needed.

Classify physically received quantities in every goods receipt as:

* Accepted
* Damaged or quarantined
* Rejected

Move only accepted quantities into sellable stock. Move damaged quantities into a non-sellable stock bucket. Keep rejected goods out of stock unless a controlled quarantine workflow records them.

Reject over-receipt by default. Accept it only under an authorized policy.

Receipt submission must be idempotent. Replaying the same receipt request must not add stock twice.

### 4.9 Sales order and order line

Record customer demand, its source, and its creator in every order. Set the creator from the authenticated staff member or integration identity.

Record product, ordered quantity, price, currency, fulfilled quantity, cancelled quantity, and allocation information in every order line.

Snapshot prices and currencies at order submission. Never let later catalogue price changes alter historical orders.

For each order line:

`outstanding_qty = ordered_qty - cancelled_qty - fulfilled_qty`

`backordered_qty = max(0, ordered_qty - cancelled_qty - fulfilled_qty - active_allocated_qty)`

Allocated-but-unfulfilled quantity remains operationally outstanding, but it is not backordered.

Derive these quantities from authoritative records or maintain them as transactional projections. Prohibit independently mutable duplicate quantities without a demonstrated performance need and protecting reconciliation tests.

### 4.10 Picking, shipment, and delivery

Collect quantities from stock through picking. Prepare them through packing. Record dispatched quantities and delivery updates in a shipment.

Reject dispatch exceeding the quantity authorized for fulfilment.

Deduct physical stock at dispatch confirmation, never at pick-list creation. Reject duplicate dispatch deductions for the same shipment.

Track order state and shipment state separately. Fulfil a sales order through multiple partial shipments where needed.

### 4.11 Inter-warehouse transfer

Move stock from a source warehouse to a destination warehouse through a transfer.

Lifecycle:

1. Requested or drafted
2. Approved
3. Source stock allocated
4. Dispatched
5. Partially or fully received at destination
6. Closed after discrepancies are resolved or recorded

Decrease source stock and move the dispatched quantity into transit at dispatch. Move accepted quantity into destination stock at receipt.

Hide transferred goods from destination availability before receipt. Record shortages, damage, and missing quantities explicitly.

### 4.12 Returns and adjustments

Inspect customer returns before deciding their stock disposition. Returned goods may enter sellable, damaged, or quarantine stock.

Process returns without implying a refund. Financial settlement stays outside the initial inventory scope.

Require an authorized reason and actor for every inventory adjustment. Preserve original history through compensating movements.

### 4.13 Identity, integrations, and audit

Assign roles and permissions to users. Restrict each user to authorized warehouses and locations through warehouse-scoped permissions.

Issue separate credentials with explicit permissions to external integrations.

Record actor, action, timestamp, affected resource, correlation identifier, and relevant change details in every audit event. Never copy credentials, tokens, or secrets into audit payloads.

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

Call other modules' application services only through explicit interfaces. Eliminate circular dependencies and hidden business operations in model signals.

## 6. State machines

Implement explicit transition functions. Reject arbitrary status updates.

### Sales order

States:

* `draft`
* `submitted`
* `confirmed`
* `in_fulfilment`
* `partially_fulfilled`
* `fulfilled`
* `cancelled`
* `rejected`

A backordered order remains confirmed or partially fulfilled while waiting for stock. Never use a single `backordered` order status when an order can contain allocated, backordered, and fulfilled quantities simultaneously.

### Reservation

* `active`
* `partially_consumed`
* `consumed`
* `released`
* `expired`
* `cancelled`

Execute transitions transactionally and idempotently.

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

Never cancel a dispatched shipment as though the goods never left the warehouse. Run a return or explicit reversal workflow instead.

### Transfer

* `draft`
* `approved`
* `dispatched`
* `partially_received`
* `received`
* `closed`
* `cancelled`

Cancel a transfer only before dispatch. After dispatch, run a controlled resolution or reversal process.

Implement and test exact transition rules in domain services.

## 7. Backorder allocation policy

Initial policy:

1. Allocate newly available stock to the oldest eligible backorder first, using creation time and a stable identifier as tie-breakers.
2. Allocate only from the warehouse selected for the order.
3. Perform allocation transactionally using the same locking or conditional-update strategy as normal reservations.
4. Exclude cancelled and already fulfilled quantities.
5. Require an explicit permission and audit reason for any staff override of priority.
6. Never silently change an order's selected warehouse to satisfy a backorder.

Encapsulate the allocation policy so it switches between automatic and staff-approved without rewriting the inventory ledger.

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
