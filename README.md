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

Prerequisites: Docker + Docker Compose, or Python 3.13 with `uv` and Node 22 with `pnpm` for local work.

### Full stack (recommended)

```bash
cp .env.example .env
docker compose up --build
# web: http://localhost:5173/
# api: http://localhost:8000/api/v1/health/
```

Services: `web` (React dev server), `api` (Django), `worker` (Celery),
`db` (PostgreSQL 17), `redis` (broker).

### Backend only

```bash
cd backend
uv venv && uv pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
pytest            # foundation tests
ruff check . && ruff format --check .
```

### Frontend only

```bash
cd frontend
pnpm install
pnpm run dev       # proxied to the API at localhost:8000
pnpm test
pnpm run build
```

Set `VITE_API_URL` to point the web app at a non-local API.

## Core rules

- Inventory alone commits physical stock changes.
- Movements are immutable; corrections are compensating movements.
- Reservations affect availability, not on-hand quantity.
- Dispatch is the default deduction point; transfer dispatch and receipt are separate events.
- Money uses exact decimals; no cross-currency aggregation without explicit conversion.

## License

MIT — see `LICENSE`.
