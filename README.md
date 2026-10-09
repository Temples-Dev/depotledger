# depotledger

Multi-warehouse inventory and fulfilment platform for wholesale and distribution businesses. Ledger-based stock truth: immutable movements + transactional balances, reservations with expiry, orders, transfers, and dispatch tracked end to end.

**Status:** Early — architecture and domain docs in progress, no implementation yet.
**Stack:** Django + Django REST Framework, React + TypeScript + Vite, PostgreSQL, Redis + Celery, Docker.
**Architecture:** Modular monolith. PostgreSQL is the source of truth.

## Why

Wholesale distributors running multiple warehouses need accurate stock across sites without overselling under concurrent orders. Spreadsheets and naive stock counters fail at partial fulfilment, backorders, transfers in transit, and returns.

depotledger models every physical change as an append-only movement, derives availability as `available = on_hand - reserved`, and commits business records + balances + movements atomically.

## What it covers

- Catalogue: products, SKUs, barcodes, categories
- Warehousing: warehouses, storage locations, warehouse-scoped access
- Inventory core: balances, immutable movement ledger, reservations / allocations, adjustments, reconciliation
- Procurement: suppliers, purchase orders, goods receipts (accepted / damaged / rejected)
- Sales: customers, sales orders, backorders, reservation allocation
- Fulfilment: picking, packing, shipments, dispatch (default stock deduction point), delivery
- Transfers: inter-warehouse dispatch → in-transit → receipt, with shortage/damage tracking
- Platform: versioned REST API (`/api/v1/`), idempotency, transactional outbox, audit events, role-based access

Out of scope for v1: general ledger / accounting, payroll, manufacturing, fleet routing, marketplace, native mobile, AI forecasting.

## Docs

- `docs/architecture/architecture-overview.md` — system context, modules, tech stack, phases
- `docs/architecture/domain-model.md` — concepts, ownership, state machines, invariants
- `docs/architecture/database-design.md` — tables, constraints, transaction boundaries
- `docs/architecture/inventory-lifecycle.md` — reservations, dispatch, receiving, transfers, concurrency

## How to run

Implementation starts at Phase 1 (see architecture overview). Until the backend/frontend scaffolds land, there is nothing to run yet.

Planned layout:

```text
depotledger/
├── backend/    # Django + DRF (config/, apps/, common/)
├── frontend/   # React + TS + Vite
├── docs/architecture/
├── docker-compose.yml      # planned: api, worker, postgres, redis
└── README.md
```

Planned quickstart (once scaffolded):

```bash
docker compose up --build
# api: http://localhost:8000/api/v1/
# web: http://localhost:5173/
```

## Core rules

- Inventory alone commits physical stock changes.
- Movements are immutable; corrections are compensating movements.
- Reservations affect availability, not on-hand quantity.
- Dispatch is the default deduction point; transfer dispatch and receipt are separate events.
- Money uses exact decimals; no cross-currency aggregation without explicit conversion.

## License

MIT — see `LICENSE`.
