# Stockflow — Architecture Overview

**Status:** Draft
**Version:** 1.0
**Architecture style:** Modular monolith
**Backend:** Django + Django REST Framework
**Frontend:** React + TypeScript + Vite
**Database:** PostgreSQL

---

## 1. Purpose

Stockflow is an inventory and fulfilment platform designed for wholesale and distribution businesses operating across multiple warehouses.

The system manages the lifecycle of inventory, from procurement and receiving through storage, reservation, order fulfilment, dispatch, delivery, transfers, and returns.

This document defines the system's architectural boundaries, major components, technology stack, data ownership, and communication patterns.

It serves as the architectural reference for implementation.

## 2. Architectural Goals

Stockflow must:

1. Maintain accurate inventory quantities across multiple warehouses.
2. Prevent overselling and conflicting inventory operations under concurrent requests.
3. Support partial fulfilment, backorders, and reservation expiry.
4. Expose a secure API for internal users and external integrations.
5. Maintain traceable records of stock movements and important business operations.
6. Support asynchronous processing without making the core inventory model unnecessarily complex.
7. Remain modular enough to evolve without prematurely introducing microservices.
8. Provide a responsive web interface for staff managing daily operations.

### 2.1 Non-functional requirements

* **Consistency:** Inventory-changing operations must be transactional.
* **Traceability:** Physical stock changes must have corresponding ledger records.
* **Security:** Access must be controlled by role, permission, and warehouse scope where applicable.
* **Reliability:** Failed asynchronous jobs and external integrations must be recoverable.
* **Maintainability:** Business rules must live in domain services rather than being scattered across API handlers.
* **Testability:** Critical inventory rules must be testable independently of the web interface.
* **Extensibility:** New integrations and business capabilities should fit into existing module boundaries.

## 3. System Context

Stockflow is initially a single-company platform supporting multiple warehouses. Company-wide configuration and catalogue data are shared across those warehouses.

The system interacts with four primary groups:

* **Internal staff:** Manage products, procurement, stock, orders, and fulfilment.
* **External systems:** Submit orders or retrieve permitted data through the API.
* **Suppliers and customers:** Participate in purchasing, sales, receiving, and delivery workflows.
* **Background workers:** Process scheduled tasks, notifications, integration events, and other work that does not need to run within the original request.

External systems do not receive direct database access. All supported operations pass through authenticated application interfaces.

## 4. High-Level Architecture

```text
                    Internal Staff
                          |
                    Web Application
                 React + TypeScript
                          |
                          | HTTPS / JSON
                          |
                    API Application
               Django REST Framework
                          |
          +---------------+----------------+
          |               |                |
      Catalogue        Inventory          Sales
          |               |                |
      Procurement     Warehousing      Fulfilment
          |               |                |
          +---------------+----------------+
                          |
                    Domain Services
                          |
                Transactional Database
                      PostgreSQL
                          |
             +------------+------------+
             |                         |
         Redis / Broker            Outbox Events
             |                         |
         Celery Workers          Integration Delivery
             |
     Notifications / Scheduled Tasks

External Systems -------- HTTPS / JSON -------- API Application
```

This is a logical view, not a requirement to deploy every component as a separate service.

In the initial deployment, the Django application can run as one deployable application, with background workers running as separate processes when needed.

## 5. Technology Stack

| Layer             | Technology                    | Responsibility                        |
| ----------------- | ----------------------------- | ------------------------------------- |
| Web frontend      | React                         | User interface                        |
| Language          | TypeScript                    | Frontend type safety                  |
| Frontend tooling  | Vite                          | Development and production builds     |
| Styling           | Tailwind CSS                  | Styling and layout                    |
| Backend           | Django                        | Application framework                 |
| API               | Django REST Framework         | HTTP endpoints and request handling   |
| Database          | PostgreSQL                    | Persistent transactional data         |
| Background jobs   | Celery                        | Asynchronous and scheduled work       |
| Message broker    | Redis initially               | Queueing background jobs              |
| API documentation | OpenAPI                       | Machine-readable API contract         |
| Automated testing | pytest / Django testing tools | Unit, integration, and API tests      |
| Deployment        | Docker                        | Reproducible application environments |

Technology choices may be revised through an explicit architecture decision, rather than changed informally across implementation.

Redis is not the authoritative inventory store. PostgreSQL remains the source of truth for stock quantities, reservations, orders, and movement records.

## 6. Backend Architecture

The backend follows a modular monolith architecture.

A modular monolith is one application with clearly defined internal modules, ownership rules, and dependencies. It avoids the operational complexity of microservices while preserving boundaries that make later evolution possible.

### 6.1 Proposed backend structure

```text
backend/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── identity/
│   ├── catalogue/
│   ├── warehousing/
│   ├── inventory/
│   ├── procurement/
│   ├── sales/
│   ├── fulfilment/
│   ├── transfers/
│   ├── integrations/
│   ├── audit/
│   └── reporting/
├── common/
│   ├── exceptions.py
│   ├── pagination.py
│   ├── permissions.py
│   └── utilities.py
├── manage.py
└── tests/
```

This is the proposed logical organization. Exact package names and whether some modules are separate Django applications can be finalized during project setup.

### 6.2 Responsibilities

**Identity**

* User accounts and authentication.
* Roles and permissions.
* Warehouse access assignments.
* Integration client credentials and scopes.

**Catalogue**

* Products, SKUs, barcodes, and categories.
* Product status and catalogue validation.

**Warehousing**

* Warehouse records and storage locations.
* Warehouse configuration and location hierarchy.

**Inventory**

* Stock balances and availability calculations.
* Immutable physical stock movement records.
* Reservation lifecycle and allocation.
* Inventory adjustments and inventory consistency rules.

**Procurement**

* Purchase orders.
* Supplier records and purchasing workflows.
* Goods receipts, including accepted, damaged, and rejected quantities.

**Sales**

* Customer records.
* Sales orders and order lines.
* Order validation, cancellation, and backorder tracking.

**Fulfilment**

* Picking, packing, shipments, dispatch, and delivery tracking.
* Coordination of order fulfilment without independently modifying inventory balances.

**Transfers**

* Inter-warehouse transfer requests.
* Dispatch and receipt of transferred goods.
* Tracking of inventory in transit.

**Integrations**

* External API integration workflows.
* Idempotency handling and event delivery.
* Integration credentials and permitted operations.

**Audit**

* Audit events for important user and system actions.
* Traceability for sensitive operations.

**Reporting**

* Operational summaries and reports.
* Read-oriented aggregation of data owned by other modules.

### 6.3 Module ownership rule

Each module owns its business rules and authoritative records.

Other modules must use the owning module's service interface for business operations instead of directly modifying its data.

For example, Procurement may request that Inventory record received stock, but Procurement must not directly update `stock_balances`.

The Inventory module is the sole authority for committing physical stock changes.

## 7. Data Architecture

PostgreSQL is the authoritative data store.

### 7.1 Core data groups

| Data group                                  | Primary ownership                     |
| ------------------------------------------- | ------------------------------------- |
| Products and categories                     | Catalogue                             |
| Warehouses and locations                    | Warehousing                           |
| Stock balances and movements                | Inventory                             |
| Reservations and allocations                | Inventory                             |
| Purchase orders and receipts                | Procurement                           |
| Sales orders and order lines                | Sales                                 |
| Pick lists and shipments                    | Fulfilment                            |
| Transfers and transfer receipts             | Transfers                             |
| Users and permissions                       | Identity                              |
| Integration clients and idempotency records | Integrations                          |
| Audit events                                | Audit                                 |
| Outbox events                               | Platform / integration infrastructure |

The final placement of shared infrastructure models may vary, but their ownership must remain explicit.

### 7.2 Stock balance and movement ledger

Stock balances provide the current inventory projection used for operational queries.

The stock movement ledger records committed physical changes. Movement records must not be silently rewritten or deleted to correct mistakes; corrections must be represented by additional movements.

Reservations affect available stock but do not themselves change physical on-hand quantities.

For ordinary sellable inventory:

`available_qty = on_hand_qty - reserved_qty`

Availability must also account for stock status and warehouse/location rules. Damaged, quarantined, and in-transit stock must not be treated as ordinarily available for sale.

### 7.3 Transaction boundaries

Operations that modify related inventory and business records must execute within appropriate database transactions.

For example, dispatching an order may need to:

1. Validate the shipment and its quantities.
2. Verify that the inventory allocation is still valid.
3. Record the physical stock movement.
4. Update the stock balance.
5. Update reservation and fulfilment records.
6. Record the audit event or an event for reliable audit processing.
7. Create an outbox event when an external notification is required.

These operations must not leave the system in a partially committed business state.

The exact transaction boundaries will be specified in the relevant service implementations and lifecycle documentation.

## 8. Request and Processing Flows

### 8.1 Internal user request

1. A staff member performs an action in the React application.
2. The frontend sends an HTTPS request to the API.
3. The API authenticates the user and checks permissions and warehouse scope.
4. The relevant module validates the request.
5. Domain services execute the business operation.
6. PostgreSQL commits the transaction.
7. The API returns a structured response.
8. The frontend updates the displayed state.

The frontend may improve usability through validation, but the backend remains responsible for enforcing business rules.

### 8.2 External order submission

1. An external client authenticates using its assigned credentials.
2. The API verifies that the client is allowed to submit orders for the requested operation and scope.
3. The API validates the payload and idempotency key.
4. The Sales module creates the order through its domain services.
5. Inventory reservation and backorder processing follow the defined business policy.
6. The transaction commits.
7. The API returns the resulting order identifier and state.

Repeated submissions using the same valid idempotency key and equivalent request must not create duplicate business effects.

### 8.3 Asynchronous processing

Some work should happen outside the original request, including:

* Sending notifications.
* Delivering integration webhooks.
* Running scheduled reservation-expiry jobs.
* Generating large reports.
* Retrying transient external integration failures.

Background jobs must be designed for retries. They must not assume that a task is executed exactly once.

For important events, use a transactional outbox: persist the event in the same transaction as the business change, then deliver it asynchronously. Delivery attempts and consumer processing must be safe against duplicates.

## 9. Inventory Consistency and Concurrency

Inventory correctness is a primary architectural requirement.

### 9.1 Required controls

* Use database transactions for multi-record inventory operations.
* Lock relevant stock balance rows or use an equivalent safe conditional-update strategy.
* Validate stock availability inside the transaction, not only before it.
* Enforce non-negative quantity constraints where applicable.
* Use idempotency for operations that may be retried.
* Prevent duplicate stock movements for the same committed business operation.
* Use explicit rules for reservation expiry and release.
* Ensure transfer dispatch and receipt are separate physical events.
* Test concurrent orders and concurrent dispatches.

### 9.2 No direct balance edits

Stock balances must be changed only through Inventory-owned operations.

Manual adjustments must record an authorized reason, quantities, affected stock, and audit information. The implementation should preserve a traceable link between each committed movement and the business operation that caused it.

### 9.3 Reconciliation

The system should provide checks that compare stock balances against the sum of applicable committed movement records.

Reconciliation must identify discrepancies for investigation. It must not silently overwrite the ledger or automatically invent corrective movements.

## 10. API Architecture

The backend exposes a versioned REST API.

The initial public API prefix is:

`/api/v1/`

Example resource paths:

```text
/api/v1/products/
/api/v1/warehouses/
/api/v1/inventory/balances/
/api/v1/orders/
/api/v1/purchase-orders/
/api/v1/transfers/
/api/v1/shipments/
```

These are illustrative routes, not the finalized API contract.

API conventions must define:

* Authentication and authorization.
* Request and response formats.
* Validation error structure.
* Pagination, filtering, and sorting.
* Idempotency requirements.
* Status codes and conflict responses.
* API versioning and compatibility.
* Rate limiting for external clients.
* OpenAPI documentation.

The API layer must remain thin. It should handle transport concerns and delegate business operations to domain services.

## 11. Frontend Architecture

The frontend is a React and TypeScript application organized by business feature.

Proposed structure:

```text
frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   │   ├── catalogue/
│   │   ├── inventory/
│   │   ├── procurement/
│   │   ├── orders/
│   │   ├── fulfilment/
│   │   ├── transfers/
│   │   └── reporting/
│   ├── lib/
│   ├── services/
│   ├── types/
│   └── main.tsx
├── public/
└── package.json
```

The frontend should use reusable components and feature-specific screens.

Responsibilities include:

* Rendering data and workflows.
* Providing forms and client-side validation.
* Presenting permission-aware navigation and actions.
* Displaying loading, empty, success, and error states.
* Supporting warehouse selection and warehouse-scoped workflows.
* Communicating with the backend through a consistent API client.

The frontend must not be treated as a security boundary. Hiding an action in the UI does not replace backend authorization.

API types should be generated from or kept consistent with the OpenAPI contract where practical.

## 12. Security Architecture

Security controls apply to both internal users and external integrations.

Required principles:

1. Deny access by default unless explicitly permitted.
2. Enforce permissions on the backend for every protected operation.
3. Enforce warehouse scope where an operation is warehouse-specific.
4. Separate user authentication from integration-client authentication.
5. Store passwords and credentials using appropriate secure mechanisms.
6. Keep secrets out of source control and logs.
7. Audit sensitive administrative and inventory operations.
8. Validate all external input.
9. Apply rate limits and abuse controls to exposed APIs.
10. Use HTTPS in deployed environments.

External integration clients must receive only the scopes and operations required for their purpose.

## 13. Deployment Architecture

The initial deployment may use Docker-based services:

```text
Deployment Environment
│
├── Frontend
│   └── Static web assets / web server
│
├── Backend
│   └── Django API application
│
├── Background Worker
│   └── Celery worker
│
├── Scheduler
│   └── Scheduled task process
│
├── PostgreSQL
│   └── Persistent application data
│
└── Redis
    └── Background task broker
```

The frontend may be served independently or through a web server in front of the API.

Production deployment must account for:

* Database backups and restore testing.
* Environment-specific configuration.
* Database migrations.
* Application and worker health checks.
* Centralized logs and operational monitoring.
* Secret management.
* TLS termination.
* Worker retry and failure handling.
* Database and queue persistence requirements.

The development environment should be reproducible and documented before production deployment is introduced.

## 14. Testing Strategy

Testing should be layered.

**Unit tests**

* Quantity calculations.
* Order and reservation rules.
* Permission policies.
* Domain service validation.

**Integration tests**

* Database transactions.
* Inventory balance and movement consistency.
* Reservation allocation and expiry.
* Goods receipt, dispatch, transfer, and returns.
* Idempotency and outbox processing.

**API tests**

* Authentication and authorization.
* Request validation.
* Response formats and status codes.
* Pagination and filtering.
* External client permissions.

**Concurrency tests**

* Two orders competing for the same stock.
* Duplicate dispatch requests.
* Reservation expiry racing with fulfilment.
* Concurrent receiving and inventory adjustments.

**End-to-end tests**

* Product creation.
* Purchase order and receiving workflow.
* Sales order and reservation workflow.
* Picking, packing, dispatch, and delivery.
* Inter-warehouse transfer.
* Returns and inventory adjustment.

Critical inventory tests must verify both the resulting balances and the corresponding ledger records.

## 15. Architectural Constraints

The following rules apply unless changed through a documented architecture decision:

* Stockflow starts as a modular monolith.
* PostgreSQL is the authoritative data store.
* Inventory is the only module allowed to commit physical stock changes.
* Physical stock movement records are immutable.
* Reservations do not directly change physical on-hand quantities.
* Dispatch is the default point at which outgoing goods are deducted from physical stock.
* Transfer dispatch and transfer receipt are distinct events.
* Business rules belong in domain services, not exclusively in API views or frontend components.
* External events must be delivered reliably and tolerate duplicate processing.
* Monetary amounts use exact decimal representations.
* Values in different currencies must not be combined without an explicit conversion policy.
* No microservices should be introduced without a demonstrated need.

## 16. Initial Implementation Order

The architecture should be implemented incrementally.

### Phase 1 — Foundation

* Repository structure and development environment.
* Django configuration and PostgreSQL connection.
* React, TypeScript, and Vite setup.
* Environment configuration.
* Automated testing and code quality tooling.
* API conventions and error handling.

### Phase 2 — Identity and catalogue

* User authentication and permissions.
* Warehouse access rules.
* Warehouses and storage locations.
* Products, SKUs, and categories.

### Phase 3 — Inventory core

* Stock balances.
* Immutable movement ledger.
* Reservation records and lifecycle.
* Inventory domain services.
* Concurrency and invariant tests.

### Phase 4 — Procurement and sales

* Suppliers and purchase orders.
* Goods receiving.
* Customers and sales orders.
* Backorders and reservation allocation.

### Phase 5 — Fulfilment and transfers

* Picking and packing.
* Shipment and dispatch.
* Delivery tracking.
* Inter-warehouse transfers.
* Returns and adjustments.

### Phase 6 — Integrations and operations

* External API access.
* Idempotency.
* Transactional outbox and background processing.
* Audit and reporting.
* Monitoring, backups, and deployment hardening.

The phases describe implementation dependencies, not a promise that every feature will be delivered before the next phase begins. Critical architectural rules and tests should be established early.

## 17. Open Architecture Decisions

The following require explicit decisions before their dependent features are finalized:

1. Whether backorders are allocated automatically or require staff approval.
2. Whether stock allocation occurs at warehouse level only or at storage-location level.
3. Whether reservation renewal is supported and under what conditions.
4. How over-receiving purchase orders is handled.
5. Which currency is used for company-level reporting and how exchange rates are sourced.
6. Which audit events require long-term retention.
7. Which operations require mandatory idempotency keys.
8. The initial authentication method and session/token strategy.
9. Whether external integrations use polling, webhooks, or both.
10. The first production deployment and backup strategy.

These decisions should be recorded in architecture decision records when finalized.

## 18. Definition of Architecture Readiness

The architecture is ready for the first implementation milestone when:

* The repository structure is established.
* The backend and frontend start successfully in development.
* PostgreSQL configuration and migrations work.
* Automated tests run reliably.
* The initial API contract and error format are defined.
* Domain modules and ownership boundaries are understood.
* Inventory invariants and transaction rules are represented in tests or explicit test plans.
* Authentication and authorization decisions are documented.
* The next implementation milestone has clear acceptance criteria.

---

**Document status:** Initial architecture baseline. Update this document when a meaningful architectural decision changes; do not use it as a substitute for detailed API, security, database, or operational specifications.
