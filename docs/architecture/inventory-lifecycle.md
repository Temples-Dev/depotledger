# depotledger — Inventory Lifecycle and Invariants

* **Status:** Approved
* **Version:** 1.0

## 1. Purpose

This document defines how depotledger changes inventory in response to reservations, receiving, dispatch, transfers, returns, and adjustments.

It supplements the domain model and database design and establishes the behavior that implementation and automated tests must enforce.

## 2. Stock vocabulary

For a sellable stock bucket:

* `on_hand_qty`: physical quantity recorded at that location.
* `reserved_qty`: quantity committed to active reservations.
* `available_qty = on_hand_qty - reserved_qty`.
* `backordered_qty`: order demand not yet allocated. This is not a stock quantity.
* `in_transit_qty`: quantity dispatched from one warehouse but not yet accepted at its destination.

Damaged and quarantined quantities are tracked separately and excluded from sellable availability.

A reservation does not reduce physical on-hand quantity. It reduces availability by increasing the reserved quantity.

## 3. Reservation and backorder example

An order requests 100 units. The selected warehouse has 60 available units.

1. Accept the order because backorders are enabled.
2. Reserve the available 60 units.
3. Record the remaining 40 units as backordered demand.
4. Keep physical on-hand at 60, reserved quantity at 60, and available quantity at zero.
5. When new stock becomes available, the backorder allocation policy may reserve some or all of the remaining 40 units.
6. When goods are dispatched, reduce physical on-hand and consume the corresponding reservation.

Never reserve unavailable stock or represent backordered demand as negative inventory.

## 4. Reservation expiry

The default reservation expiry is 24 hours after creation.

When a reservation expires:

* Release only the allocation quantity that remains active.
* Decrease `reserved_qty` by exactly the released amount.
* Record an expiration event.
* Leave the sales order in its existing business state; expiry does not cancel the order.
* Make the released stock available to other eligible demand.
* Never release quantity already consumed by dispatch.
* Make expiry safe to execute repeatedly or concurrently.

Use the database clock for expiry decisions. Workers must lock or safely claim eligible reservations before processing them.

The reservation state change and balance release must commit atomically.

If reservation renewal is introduced, record the new expiry and the actor or reason. Renewal must not silently extend every reservation indefinitely.

## 5. Partial fulfilment

For each order line:

`outstanding_qty = ordered_qty - cancelled_qty - fulfilled_qty`

`backordered_qty = max(0, ordered_qty - cancelled_qty - fulfilled_qty - active_allocated_qty)`

These values must be derived from authoritative order and reservation/allocation records, or maintained as transactional projections with reconciliation tests.

### Example

An order line has:

* Ordered quantity: 100
* Cancelled quantity: 0
* Fulfilled quantity: 20
* Active allocated quantity: 30

The resulting quantities are:

* Outstanding: 80
* Allocated but unfulfilled: 30
* Backordered: 50

A partial shipment consumes only the reservation/allocation associated with the dispatched quantity. Any undispatched reservation remains active unless the workflow explicitly releases it.

## 6. Dispatch commit point

Under depotledger's default policy, picking and packing do not reduce physical stock. Stock is deducted when dispatch is committed.

For a dispatched quantity:

1. Decrease sellable `on_hand_qty`.
2. Decrease the corresponding active `reserved_qty` by the quantity consumed from the reservation.
3. Append an immutable negative stock movement.
4. Mark the shipment as dispatched.
5. Update order-line fulfilled quantities.
6. Commit all related changes in one transaction.

The operation must verify that the shipment is in a dispatchable state and the requested quantity is authorized.

Repeating the same idempotent dispatch command must return the prior result without repeating the stock change.

If a shipment is cancelled before dispatch, release its reservations as appropriate. If goods have already left the warehouse, do not simply reverse the dispatch record; use a return or explicit reversal workflow that records the physical event.

## 7. Goods receiving

A goods receipt classifies received quantities as:

* Accepted
* Damaged or quarantined
* Rejected

Only accepted goods increase sellable on-hand. Damaged goods enter a non-sellable bucket. Rejected goods do not enter stock unless an explicit controlled quarantine workflow records them.

For every posted receipt:

1. Validate the purchase order and outstanding quantities.
2. Apply the over-receipt policy.
3. Record receipt details and the associated stock movements.
4. Update balances and purchase-order state atomically.
5. Apply idempotency protection to prevent duplicate stock additions.

Accepted, damaged, and rejected quantities must remain distinguishable throughout the receipt lifecycle.

## 8. Inter-warehouse transfers

A transfer is a staged inventory movement, not a direct edit to two warehouse balances.

### 8.1 Dispatch from source

* Verify that the transfer is approved.
* Verify that the source has sufficient available stock.
* Reduce source on-hand quantity.
* Record the dispatched quantity as in transit.
* Create source and in-transit movement records.
* Mark the dispatch as posted.

All changes must commit atomically.

### 8.2 Receive at destination

* Validate the receipt against the outstanding in-transit quantity.
* Reduce in-transit quantity for the received portion.
* Move accepted quantity into destination sellable stock.
* Move damaged quantity into a non-sellable destination bucket.
* Record missing or short quantities explicitly.
* Resolve the in-transit quantity consistently.
* Prevent duplicate receipt processing.

Destination stock must not be available before the destination receipt is posted.

## 9. Returns and adjustments

Customer returns require inspection before stock is classified.

* Accepted goods may return to sellable stock.
* Damaged goods enter a damaged bucket.
* Uncertain goods remain quarantined until their disposition is decided.

An inventory adjustment must include:

* Reason code
* Actor
* Affected product and stock bucket
* Quantity delta
* Approval when required by policy
* Corresponding immutable stock movement when posted

Never silently overwrite a balance. Record a compensating movement and preserve the original history.

## 10. Transaction and concurrency rules

Every stock-changing command must:

1. Authenticate and authorize the actor.
2. Validate the requested state transition.
3. Begin a database transaction.
4. Lock or conditionally update relevant balance, reservation, and order rows.
5. Recalculate eligibility using the current state.
6. Write the business record, balance changes, movement or reservation events, audit entry, and outbox event as applicable.
7. Commit only if all required writes succeed.

Never hold a database transaction open across an external service call. Publish downstream events through the outbox after the business transaction commits.

### 10.1 Preventing overselling

Never trust a pre-transaction availability read. Another request reserves the same stock before the first request commits.

Use `select_for_update()` or an atomic conditional update so that the availability check and reservation update are serialized. When stock is gone at lock time, allocate only the remaining available quantity or return the defined business result.

### 10.2 Preventing duplicate effects

Each externally retriable command must use an idempotency mechanism. The idempotency record and business operation must be coordinated so concurrent retries cannot execute the stock change twice.

A database transaction must roll back the complete operation if any required step fails.

## 11. Required correctness tests

The following scenarios must be covered by automated tests:

* Two orders concurrently attempt to reserve the last available units; total reservations never exceed stock.
* A reservation expiry worker and a dispatch worker race; quantity is neither released nor consumed twice.
* The same receipt request is submitted repeatedly; stock increases once.
* The same dispatch request is submitted repeatedly; stock decreases once.
* A transfer is dispatched but not yet received; destination availability remains unchanged.
* A transfer receipt is retried; destination stock increases once.
* A damaged receipt increases damaged or quarantine quantity but not sellable availability.
* A cancelled order line cannot receive a new allocation.
* A partial shipment updates fulfilled, allocated, and backordered quantities consistently.
* An inventory adjustment cannot create negative sellable stock.
* A failed transaction leaves no partial balance, movement, reservation, or shipment update.
* Concurrent receiving operations cannot exceed the allowed purchase-order quantities.
* Unauthorized warehouse access is rejected by the backend.
* Ledger and balance reconciliation detects discrepancies.

## 12. Reconciliation

Provide a management command that:

1. Reconstructs or verifies physical balances from movement history using the defined movement semantics.
2. Compares computed balances with stored balances.
3. Checks active reservation allocations against reserved quantities.
4. Identifies expired reservations that have not been processed.
5. Reports discrepancies without silently rewriting production data.

Physical stock reconciliation and reservation reconciliation must be separate because reservations affect reserved availability but not physical on-hand quantity.

Represent opening inventory through explicit opening-stock movements so physical balance reconstruction starts from a known point.

Run any automated correction through a deliberate, auditable process. Never silently change balances.
