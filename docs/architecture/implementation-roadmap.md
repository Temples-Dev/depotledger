# depotledger — Implementation Roadmap

## 1. Purpose

This document defines the implementation sequence for depotledger, an inventory and fulfilment platform designed for wholesale and distribution businesses operating across multiple warehouses.

The roadmap prioritizes correctness, maintainability, and verifiable progress. Each milestone must produce a working, testable increment rather than a collection of unfinished features.

## 2. Implementation Principles

1. **Build the foundation first.** Establish the project structure, development environment, configuration, and testing infrastructure before implementing business workflows.
2. **Protect inventory integrity.** Stock changes must be transactional, auditable, and resistant to concurrent operations.
3. **Keep the architecture modular.** Implement a modular monolith with clear domain boundaries. Do not introduce microservices without a demonstrated need.
4. **Test business rules, not just endpoints.** Inventory and order workflows need domain-level, integration, concurrency, and failure-path tests.
5. **Document decisions.** Update the architecture and API documentation when implementation reveals a necessary change.
6. **Deliver incrementally.** Every milestone must leave the application in a runnable state.
7. **Avoid premature expansion.** Complete the core inventory lifecycle before implementing advanced reporting, external integrations, or optimization features.

## 3. Technology Baseline

| Layer                 | Technology                                          |
| --------------------- | --------------------------------------------------- |
| Backend               | Python, Django, Django REST Framework               |
| Frontend              | React, TypeScript, Vite                             |
| Styling               | Tailwind CSS and reusable UI components             |
| Database              | PostgreSQL                                          |
| Background processing | Celery and Redis, when required                     |
| API documentation     | OpenAPI                                             |
| Backend testing       | pytest and Django/DRF testing tools                 |
| Frontend testing      | Vitest and React Testing Library                    |
| Version control       | Git                                                 |
| Deployment            | Docker-based development and deployment environment |

Use compatible, supported versions and pin dependencies. Add infrastructure only when a defined requirement justifies it.

## 4. Milestone Overview

| Milestone | Focus                           | Completion outcome                                                      |
| --------- | ------------------------------- | ----------------------------------------------------------------------- |
| M0        | Requirements and decisions      | Initial scope and business rules are agreed                             |
| M1        | Project foundation              | Backend, frontend, database, and tests run locally                      |
| M2        | Identity and access             | Users, roles, permissions, and warehouse scope work                     |
| M3        | Catalogue and warehouses        | Products, SKUs, warehouses, and locations are manageable                |
| M4        | Inventory core                  | Stock balances and immutable movement records are reliable              |
| M5        | Reservations and backorders     | Availability, allocation, and expiry rules work                         |
| M6        | Procurement and receiving       | Purchase orders and partial goods receiving update inventory            |
| M7        | Sales orders                    | Orders, line quantities, and order-level state transitions work         |
| M8        | Fulfilment and dispatch         | Picking, packing, dispatch, and partial fulfilment work                 |
| M9        | Transfers, returns, adjustments | Other major stock-changing workflows are supported                      |
| M10       | Frontend workflows              | Core operational workflows are usable through the web interface         |
| M11       | Integration and hardening       | External API, audit, observability, and reliability checks are complete |
| M12       | Deployment readiness            | The application can be deployed and operated safely                     |

Overlap milestones where dependencies permit. Never let a later milestone bypass the correctness requirements of an earlier one.

---

## 5. Detailed Milestones

### M0 — Requirements and Domain Decisions

**Objective:** Resolve the minimum decisions needed to implement the system consistently.

Tasks:

* [ ] Review `domain-model.md`.
* [ ] Review `database-design.md`.
* [ ] Review `inventory-lifecycle.md`.
* [ ] Review `architecture-overview.md`.
* [ ] Review `api-specification.md`.
* [ ] Review `security-and-permissions.md`.
* [ ] Confirm order, reservation, fulfilment, and shipment state transitions.
* [ ] Confirm how backorders are allocated and whether allocation is automatic.
* [ ] Define stock statuses and which statuses are available for sale.
* [ ] Decide whether reservations can be renewed.
* [ ] Define the initial authentication approach.
* [ ] Define adjustment approval requirements.
* [ ] Record unresolved decisions in a decision log.

**Acceptance criteria:**

* Core domain terms have one consistent meaning.
* Inventory-changing operations have explicit rules.
* Security and warehouse-access expectations are documented.
* Remaining unresolved decisions are identified and do not block the first milestone.

### M1 — Project Foundation

**Objective:** Establish a reproducible development environment and a maintainable codebase.

Tasks:

* [ ] Create the Git repository structure.
* [ ] Initialize the Django backend.
* [ ] Initialize the React, TypeScript, and Vite frontend.
* [ ] Configure PostgreSQL.
* [ ] Add environment-based configuration and an example environment file.
* [ ] Configure dependency management and lockfiles.
* [ ] Add database migrations.
* [ ] Configure formatting, linting, and automated tests.
* [ ] Add Docker-based local development.
* [ ] Add a health-check endpoint.
* [ ] Add a consistent API error format.
* [ ] Configure CI to run checks on every pull request.
* [ ] Document setup instructions in `README.md`.

Repository structure:

```text
depotledger/
├── backend/
│   ├── config/
│   ├── modules/
│   │   ├── identity/
│   │   ├── catalogue/
│   │   ├── warehousing/
│   │   ├── inventory/
│   │   ├── procurement/
│   │   ├── sales/
│   │   ├── fulfilment/
│   │   ├── transfers/
│   │   └── audit/
│   ├── tests/
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── features/
│   │   ├── components/
│   │   └── lib/
│   └── tests/
├── docs/
│   └── architecture/
├── infrastructure/
├── .github/
│   └── workflows/
├── .env.example
├── .gitignore
└── README.md
```

Start from this structure. Create each module as its implementation milestone begins.

**Acceptance criteria:**

* A developer can follow the README to run the application locally.
* The backend connects to PostgreSQL.
* Database migrations run successfully.
* The frontend can communicate with the backend.
* Health checks work.
* CI executes formatting, linting, and tests.
* Secrets are not committed to Git.

### M2 — Identity and Access Control

**Objective:** Establish authentication and authorization before exposing operational data.

Tasks:

* [ ] Implement the selected authentication mechanism.
* [ ] Implement users, roles, and permissions.
* [ ] Implement warehouse-level access restrictions.
* [ ] Define a consistent permission-checking approach.
* [ ] Add administrative user and role management.
* [ ] Add audit events for security-sensitive operations.
* [ ] Add tests for unauthorized and out-of-scope access.

**Acceptance criteria:**

* Unauthenticated requests cannot access protected endpoints.
* Users cannot perform operations outside their permissions.
* Warehouse-scoped users cannot access unauthorized warehouse data.
* Integration clients cannot use permissions intended only for human users.
* Privileged actions are auditable.
* Authorization is enforced on the backend, not merely hidden in the frontend.

### M3 — Product Catalogue and Warehouses

**Objective:** Create the master data needed by inventory operations.

Tasks:

* [ ] Implement product categories.
* [ ] Implement products and globally unique SKUs.
* [ ] Implement product status and basic product attributes.
* [ ] Implement barcode support where required.
* [ ] Implement warehouses.
* [ ] Implement optional storage locations.
* [ ] Implement customers and suppliers.
* [ ] Add list, detail, create, and update endpoints.
* [ ] Add search, filtering, and pagination.
* [ ] Add the initial frontend screens for catalogue and warehouse management.

**Acceptance criteria:**

* Authorized users can create and maintain products and warehouses.
* Duplicate SKUs are rejected.
* Inactive products cannot be used in new transactions where prohibited.
* Warehouse and location references are validated.
* Lists are paginated and respect access restrictions.
* Catalogue changes do not silently rewrite historical transaction records.

### M4 — Inventory Core

**Objective:** Implement the authoritative mechanism for recording and querying stock.

This is the most important technical milestone. Other modules must use this mechanism rather than editing stock balances directly.

Tasks:

* [ ] Implement stock balances by product, warehouse, location, and stock status.
* [ ] Implement immutable stock movement records.
* [ ] Define the permitted inventory movement types.
* [ ] Implement a single domain service for posting inventory movements.
* [ ] Update balances and movement records within the same database transaction.
* [ ] Add locking or conditional updates to protect concurrent changes.
* [ ] Add stock movement history endpoints.
* [ ] Add balance lookup and reconciliation utilities.
* [ ] Add tests for rollback, duplicate requests, and concurrent updates.

**Acceptance criteria:**

* Every committed physical stock change has a corresponding movement record.
* A failed transaction cannot leave the balance updated without its movement record, or vice versa.
* Direct balance editing is not available through ordinary application workflows.
* Non-negative stock constraints are enforced on every reservable bucket.
* Damaged and quarantined stock is not treated as sellable stock.
* In-transit stock is not counted as available at the destination before receipt.
* Reconciliation can detect differences between recorded movements and balance projections.

**Required invariant:**

The stock movement ledger is the durable record of physical stock changes. The stock balance is a current projection that can be checked against that ledger.

### M5 — Reservations and Backorders

**Objective:** Make stock allocation reliable before implementing the full order lifecycle.

Tasks:

* [ ] Implement reservation records and their lifecycle.
* [ ] Implement reservation allocations against eligible stock.
* [ ] Implement reservation events for creation, allocation, release, expiry, and consumption.
* [ ] Calculate available stock.
* [ ] Implement reservation expiry using the configured 24-hour default.
* [ ] Implement backorder quantity calculations.
* [ ] Prevent two concurrent requests from reserving the same available units.
* [ ] Define what happens when an order changes or is cancelled.
* [ ] Add tests for partial allocation and reservation expiry.

**Acceptance criteria:**

* Reservations reduce available quantity but do not reduce physical on-hand quantity.
* Expiring a reservation releases only its remaining active allocations.
* Reservation expiry does not automatically cancel the underlying order.
* Fulfilled and cancelled quantities are excluded from outstanding demand.
* Duplicate requests cannot create duplicate reservations.
* Reservation and backorder quantities remain consistent under concurrent activity.

Use the following definitions:

```text
outstanding_qty =
    ordered_qty - cancelled_qty - fulfilled_qty

backordered_qty =
    max(
        0,
        ordered_qty
        - cancelled_qty
        - fulfilled_qty
        - active_allocated_qty
    )
```

Validate these definitions against the domain model before implementation. Do not independently reimplement these calculations in the frontend.

### M6 — Procurement and Goods Receiving

**Objective:** Bring stock into the system through traceable purchasing workflows.

Tasks:

* [ ] Implement purchase orders and purchase-order lines.
* [ ] Implement purchase-order state transitions.
* [ ] Implement goods receipts and receipt lines.
* [ ] Support partial receiving.
* [ ] Record accepted, damaged, and rejected quantities separately.
* [ ] Post accepted quantities through the inventory service.
* [ ] Support multiple receipts against a purchase order.
* [ ] Define over-receipt policy.
* [ ] Add supplier return support when the receiving workflow is stable.

**Acceptance criteria:**

* A purchase order can be received in multiple deliveries.
* Each receipt is traceable to its purchase order and supplier.
* Accepted stock increases physical on-hand quantity only when the receipt is posted.
* Damaged and rejected quantities are not made available for sale.
* Reject duplicate receipt posting without increasing stock twice.
* Purchase-order status reflects received, outstanding, and cancelled quantities accurately.

### M7 — Sales Orders

**Objective:** Introduce customer demand and connect it to the reservation system.

Tasks:

* [ ] Implement customers and customer references.
* [ ] Implement sales orders and order lines.
* [ ] Support multiple currencies for orders and purchases.
* [ ] Store transaction currency and agreed price snapshots.
* [ ] Implement order submission and cancellation rules.
* [ ] Integrate order creation with stock allocation.
* [ ] Support partial allocation and backorders.
* [ ] Implement order history and status transitions.
* [ ] Add order validation and business-rule tests.

**Acceptance criteria:**

* Orders cannot contain invalid products or quantities.
* Order status changes follow documented transition rules.
* Partial allocation is supported.
* Order quantities remain consistent across ordered, cancelled, allocated, backordered, and fulfilled amounts.
* Currency values use exact decimal representations.
* Values in different currencies are not added together without an explicit conversion rule.

### M8 — Picking, Packing, and Dispatch

**Objective:** Turn allocated orders into traceable physical fulfilment.

Tasks:

* [ ] Implement pick lists.
* [ ] Implement picking confirmation.
* [ ] Implement packing records or equivalent shipment preparation.
* [ ] Implement shipments and shipment lines.
* [ ] Support partial fulfilment and multiple shipments per order.
* [ ] Implement dispatch confirmation.
* [ ] Post physical stock deductions at dispatch.
* [ ] Implement shipment tracking references and delivery status.
* [ ] Add tests for partial shipments and duplicate dispatch requests.

**Acceptance criteria:**

* Picking does not itself reduce physical on-hand quantity.
* Dispatch is the default physical stock deduction point.
* Dispatch consumes the relevant allocations and records the physical stock movement in one transaction.
* A shipment cannot dispatch more stock than is eligible and allocated.
* Duplicate dispatch requests do not deduct stock twice.
* An order can be partially fulfilled while its remaining quantities stay outstanding or backordered.
* Shipment status is tracked separately from sales-order status.

### M9 — Transfers, Returns, and Adjustments

**Objective:** Support the remaining major stock-changing workflows.

Tasks:

* [ ] Implement warehouse transfers.
* [ ] Track transfer dispatch and receipt separately.
* [ ] Record stock in transit.
* [ ] Implement customer returns.
* [ ] Support inspection and disposition of returned stock.
* [ ] Implement inventory adjustments with reasons.
* [ ] Apply adjustment approval rules where configured.
* [ ] Add tests for failed receipts, partial transfers, and duplicate actions.

**Acceptance criteria:**

* Dispatching a transfer removes stock from the source's available inventory and records in-transit stock.
* Receiving a transfer makes the accepted quantity available at the destination.
* Damaged or missing quantities are handled explicitly.
* Returned goods are not automatically treated as sellable before inspection when inspection is required.
* Every adjustment records a reason, actor, timestamp, and associated movement.
* Sensitive adjustments follow the required approval process.

### M10 — Operational Frontend

**Objective:** Provide usable interfaces for the completed backend workflows.

Tasks:

* [ ] Implement authentication and navigation.
* [ ] Implement dashboard summaries based on reliable backend data.
* [ ] Implement product and warehouse management screens.
* [ ] Implement inventory balances and movement history.
* [ ] Implement reservations and stock availability views.
* [ ] Implement purchase orders and receiving screens.
* [ ] Implement sales order management.
* [ ] Implement picking, packing, and dispatch screens.
* [ ] Implement transfer and adjustment screens.
* [ ] Add loading, empty, validation, and error states.
* [ ] Generate or maintain typed API clients from the OpenAPI schema.
* [ ] Add frontend component and workflow tests.

**Acceptance criteria:**

* Users can complete the main operational workflows without directly calling the API.
* UI actions respect backend authorization.
* Error messages are understandable and do not expose sensitive internal details.
* Quantities and monetary values use consistent formatting.
* The UI does not calculate authoritative stock availability independently.
* Critical actions provide confirmation and clearly communicate their result.

### M11 — External API, Audit, and Reliability

**Objective:** Make the platform safe for integration and routine operations.

Tasks:

* [ ] Finalize external integration authentication and scopes.
* [ ] Implement idempotency for supported state-changing endpoints.
* [ ] Implement the transactional outbox for reliable event publication.
* [ ] Add webhook delivery and retry handling if required.
* [ ] Add administrative audit-log search.
* [ ] Add structured application logging.
* [ ] Add error monitoring and operational health checks.
* [ ] Add rate limiting and request validation.
* [ ] Test retries, timeouts, and partial failures.
* [ ] Add database backup and restoration procedures.

**Acceptance criteria:**

* Retried integration requests do not duplicate protected operations.
* Integration clients cannot access resources outside their assigned permissions.
* External events are not published for transactions that roll back.
* Failed background jobs can be retried safely.
* Sensitive data and credentials are not written to ordinary logs.
* Audit events identify the actor, action, target, time, and relevant context.
* Backup restoration has been tested, not merely documented.

### M12 — Deployment Readiness

**Objective:** Prepare depotledger for controlled use in a real operating environment.

Tasks:

* [ ] Configure production settings separately from development settings.
* [ ] Configure HTTPS and secure cookie settings.
* [ ] Configure secret management.
* [ ] Apply database migrations through a controlled deployment process.
* [ ] Configure background workers and scheduled jobs if used.
* [ ] Configure database backups and retention.
* [ ] Verify restoration procedures.
* [ ] Establish application and database monitoring.
* [ ] Document deployment, rollback, and recovery procedures.
* [ ] Run end-to-end and permission-boundary tests.
* [ ] Conduct a pilot with representative warehouse workflows.

**Acceptance criteria:**

* Production configuration does not rely on development defaults.
* Migrations and deployment steps are reproducible.
* Backups can be restored into a usable environment.
* Critical workflows have passed end-to-end tests.
* Operational errors can be diagnosed using logs and monitoring.
* Known limitations and recovery procedures are documented.
* Release approval is based on test evidence rather than feature completion alone.

---

## 6. Definition of Done

An endpoint or interface existing does not complete a feature.

Ship every feature against the following criteria:

* [ ] Business rules are documented.
* [ ] Data model and migrations are implemented.
* [ ] Backend validation and authorization are implemented.
* [ ] Database transactions preserve invariants.
* [ ] Duplicate requests and retry behavior are addressed.
* [ ] Automated tests cover success, failure, and boundary cases.
* [ ] API documentation is updated.
* [ ] Audit requirements are implemented.
* [ ] Frontend behavior and error states are complete if the feature has a UI.
* [ ] CI checks pass.
* [ ] Relevant architecture documentation is updated.

Prove concurrency, transaction rollback, and duplicate-request behavior correct for every inventory-modifying feature.

## 7. Testing Strategy

### Unit tests

Test isolated domain rules, calculations, state transitions, and validation.

Examples:

* Outstanding and backordered quantity calculations.
* Permitted order transitions.
* Reservation expiry behavior.
* Currency and quantity validation.

### Integration tests

Test the interaction between the API, database, domain services, and background jobs.

Examples:

* Receiving accepted goods creates the correct inventory movement.
* Dispatch updates stock and shipment state atomically.
* An unauthorized user cannot access a restricted warehouse.
* Replaying an idempotent request does not repeat its effect.

### Concurrency tests

Test operations that can conflict when requests execute simultaneously.

Examples:

* Two orders attempt to reserve the same stock.
* Two workers attempt to dispatch the same shipment.
* A reservation expires while an order is being fulfilled.

### End-to-end tests

Test complete workflows through the API and, once available, the frontend.

Examples:

* Receive goods, create an order, reserve stock, pick, dispatch, and verify the final balance.
* Create an order with insufficient stock, receive replenishment, and fulfil the outstanding quantity.
* Transfer stock between warehouses and verify source, in-transit, and destination quantities.

## 8. Initial Delivery Target

The first meaningful delivery must be a small but complete vertical slice, not a large collection of unfinished modules.

First slice:

1. Run the application locally.
2. Authenticate an authorized user.
3. Create a product and two warehouses.
4. Record an initial stock receipt through the inventory service.
5. View the resulting balance and movement history.
6. Attempt a second operation that would violate a stock invariant and verify that it is rejected.
7. Run the automated tests in CI.

This slice proves that the foundation, authorization, catalogue, inventory service, database, and testing process work together.

## 9. Scope Control

Keep the following features outside the initial delivery unless a concrete business requirement makes them necessary:

* Full accounting and general ledger.
* Payroll and human resources.
* Manufacturing resource planning.
* Fleet and route optimization.
* Native mobile applications.
* AI-driven forecasting.
* Microservice decomposition.
* Complex multi-company tenancy.

Record these as future possibilities. Do not let them delay the core inventory lifecycle.

## 10. Progress Tracking

Track each task using one of these states:

* **Not started**
* **In progress**
* **Blocked**
* **In review**
* **Done**

Complete a milestone only when its acceptance criteria are satisfied and the relevant tests pass.

Keep implementation issues small enough to review independently. Give each issue its domain, expected behavior, acceptance criteria, and required tests.

## 11. Immediate Next Steps

Start with M0 and M1.

1. Create the repository and documentation structure.
2. Review unresolved decisions that affect the foundation.
3. Initialize Django, PostgreSQL, and the React frontend.
4. Establish migrations, test execution, formatting, linting, and CI.
5. Implement the first health check and verify local setup.
6. Begin identity and catalogue work only after the foundation is reproducible.

Implement one verified layer at a time. Keep the codebase runnable throughout development.
