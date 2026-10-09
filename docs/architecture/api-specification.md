# depotledger — API Specification

**Status:** Approved
**Version:** 1.0
**API style:** REST over HTTPS
**Base path:** `/api/v1/`
**Request/response format:** JSON
**Backend:** Django REST Framework
**Contract format:** OpenAPI

---

## 1. Purpose

This document defines the API contract for depotledger, an inventory and fulfilment platform for wholesale and distribution businesses operating across multiple warehouses.

It establishes conventions for:

* Resource naming and HTTP methods.
* Authentication and authorization.
* Request and response formats.
* Validation and error handling.
* Pagination, filtering, and sorting.
* Inventory operations and concurrency.
* Idempotency and safe retries.
* External integrations.
* API versioning and compatibility.

The API is the communication boundary between the React frontend, the Django backend, and authorized external systems.

The API must not expose direct database access or allow clients to bypass domain rules.

## 2. API Design Principles

1. **Resource-oriented:** Represent business entities through predictable resource URLs.
2. **Explicit operations:** Use dedicated action endpoints when an operation represents a business transition rather than ordinary CRUD.
3. **Backend-enforced rules:** Validate all business rules on the server.
4. **Consistent responses:** Use a shared format for errors, pagination, and resource representations.
5. **Safe retries:** Prevent repeated requests from creating duplicate business effects.
6. **Traceability:** Return resource identifiers and request correlation identifiers.
7. **Least privilege:** Enforce permissions and warehouse access for every protected operation.
8. **Contract-first:** Maintain an OpenAPI specification and use it to keep frontend types and API documentation consistent.
9. **No direct inventory mutation:** Clients must use approved inventory operations rather than editing stock balances directly.

---

## 3. Base URL and Versioning

All endpoints use the `/api/v1/` prefix.

Example:

```text
https://api.example.com/api/v1/products/
```

The production hostname is deployment-specific.

### 3.1 Versioning policy

The version in the URL represents the major API contract version.

Compatible additions may include:

* New endpoints.
* New optional request fields.
* New response fields, provided clients are expected to tolerate unknown fields.
* New filter options.

Breaking changes require a new API version or an explicitly managed migration strategy.

Existing field meanings must not change silently.

### 3.2 Trailing slashes

Collection and resource URLs use trailing slashes consistently.

Example:

```text
GET /api/v1/products/
GET /api/v1/products/{product_id}/
```

Clients must use the documented paths rather than relying on automatic redirects.

---

## 4. Request Conventions

### 4.1 Content type

Requests with JSON bodies must use:

```http
Content-Type: application/json
```

Clients declare JSON response expectations with:

```http
Accept: application/json
```

### 4.2 Identifiers

API resources use UUID identifiers unless a documented exception exists.

Example:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

IDs are opaque identifiers. Clients must not depend on their internal structure or generation order.

### 4.3 Dates and timestamps

* Timestamps use ISO 8601 with an explicit timezone, normally UTC.
* Date-only values use `YYYY-MM-DD`.
* Clients treat every timestamp as timezone-aware.
* The backend controls authoritative timestamps.

Example:

```json
{
  "created_at": "2026-10-09T09:30:00Z"
}
```

### 4.4 Decimal quantities and monetary values

Inventory quantities and monetary amounts must use appropriate decimal representations.

API JSON must represent quantities and monetary values as decimal strings to avoid floating-point precision loss across clients.

Example:

```json
{
  "quantity": "12.500",
  "unit_price": "49.99",
  "currency": "GHS"
}
```

The exact scale and permitted precision must be defined for each field.

Clients must not send binary floating-point values as the authoritative representation of quantities or money.

### 4.5 Boolean values

Use JSON booleans:

```json
{
  "is_active": true
}
```

Do not encode booleans as `"true"`, `"false"`, `"yes"`, or `"no"` strings.

---

## 5. Authentication

depotledger supports internal users and external integration clients. Their authentication and authorization rules must be separate.

### 5.1 Internal users

The initial authentication mechanism must be selected before protected frontend endpoints are implemented.

Preferred deployment-compatible options include:

* Secure server-managed sessions using `HttpOnly`, `Secure`, and appropriate `SameSite` cookie settings.
* A properly implemented token-based authentication mechanism when required by deployment or client architecture.

For a first-party React application, secure session authentication is a reasonable default when the frontend and API deployment allow it.

If cookie-based authentication is used, unsafe methods must enforce CSRF protection.

The final choice must be documented before implementation. Do not combine multiple authentication mechanisms casually.

### 5.2 External integration clients

External integrations authenticate through individually managed client credentials.

The implementation must define:

* Credential issuance and rotation.
* Credential revocation.
* Allowed scopes and operations.
* Rate limits.
* Expiration or renewal policy.
* Secure storage and transport.
* Audit records for credential administration.

Long-lived secrets must not be placed in URLs or exposed in frontend code.

### 5.3 Unauthenticated requests

Protected endpoints return `401 Unauthorized` when authentication is missing or invalid.

Example:

```json
{
  "error": {
    "code": "authentication_required",
    "message": "Authentication is required.",
    "details": {}
  }
}
```

---

## 6. Authorization and Warehouse Scope

Authentication establishes who or what is making the request. Authorization determines which operations it may perform.

### 6.1 Permission checks

The backend must enforce permissions for:

* Reading and modifying catalogue records.
* Viewing inventory.
* Receiving purchase orders.
* Creating and approving adjustments.
* Creating and fulfilling sales orders.
* Dispatching shipments.
* Initiating and receiving transfers.
* Managing users and permissions.
* Managing integration clients.
* Accessing reports and audit records.

The frontend hides unavailable actions, and the backend enforces authorization on every request.

### 6.2 Warehouse access

Warehouse-specific operations must validate the caller's access to the relevant warehouse.

For example, access to Warehouse A must not automatically grant access to Warehouse B.

A request involving multiple warehouses, such as a transfer, must authorize both the source and destination operations according to the caller's permissions.

### 6.3 Permission failure

Return `403 Forbidden` when the caller is authenticated but lacks the required permission.

Where revealing the existence of a protected resource would itself disclose sensitive information, the implementation may return `404 Not Found` instead. Apply this policy consistently.

---

## 7. Standard Response Formats

### 7.1 Successful resource response

A single-resource request returns the resource directly unless an endpoint documents a different structure.

Example:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sku": "RICE-25KG",
  "name": "Rice, 25 kg",
  "is_active": true,
  "created_at": "2026-10-09T09:30:00Z"
}
```

### 7.2 Collection response

List endpoints use a consistent pagination envelope:

```json
{
  "count": 125,
  "next": "https://api.example.com/api/v1/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sku": "RICE-25KG",
      "name": "Rice, 25 kg",
      "is_active": true
    }
  ]
}
```

* `count` is the total number of matching records for the query.
* `next` contains the next-page URL or `null`.
* `previous` contains the previous-page URL or `null`.
* `results` contains the current page.

Sensitive fields must not appear merely because they exist on the underlying database model.

### 7.3 Error response

All API errors use a common envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid data.",
    "details": {
      "sku": [
        "A product with this SKU already exists."
      ]
    }
  }
}
```

Fields:

| Field           | Meaning                                        |
| --------------- | ---------------------------------------------- |
| `error.code`    | Stable machine-readable error identifier       |
| `error.message` | Human-readable summary                         |
| `error.details` | Optional structured field or operation details |

Clients branch on error codes, not human-readable messages.

### 7.4 Request correlation

Responses must include a request identifier, preferably through a response header such as:

```http
X-Request-ID: 2c1f6d1a-5e5f-4e8d-bd61-5d8d1c3e6a90
```

The identifier must be recorded in application logs. Clients can provide it when reporting a failure.

Do not expose stack traces, SQL statements, credentials, or internal exception details in API responses.

---

## 8. HTTP Status Codes

| Status                       | Meaning                                                 | Typical use                                             |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| `200 OK`                     | Request succeeded                                       | Read or successful update                               |
| `201 Created`                | Resource created                                        | Product, order, purchase order                          |
| `202 Accepted`               | Processing accepted but not completed                   | Explicitly asynchronous operation                       |
| `204 No Content`             | Success without response body                           | Successful deletion where permitted                     |
| `400 Bad Request`            | Invalid request structure or business input             | Validation failure                                      |
| `401 Unauthorized`           | Missing or invalid authentication                       | Authentication failure                                  |
| `403 Forbidden`              | Operation not permitted                                 | Permission failure                                      |
| `404 Not Found`              | Resource does not exist or is not visible               | Missing resource                                        |
| `405 Method Not Allowed`     | HTTP method unsupported                                 | Invalid method                                          |
| `409 Conflict`               | Request conflicts with current state                    | Duplicate operation, invalid transition, stock conflict |
| `415 Unsupported Media Type` | Unsupported content type                                | Non-JSON body where JSON is required                    |
| `422 Unprocessable Content`  | Optional alternative for structured semantic validation | Use only if adopted consistently                        |
| `429 Too Many Requests`      | Rate limit exceeded                                     | Excessive requests                                      |
| `500 Internal Server Error`  | Unexpected server failure                               | Unhandled server error                                  |
| `503 Service Unavailable`    | Service temporarily unavailable                         | Maintenance or temporary dependency outage              |

For the initial implementation, prefer `400` for validation errors and `409` for state or concurrency conflicts. Avoid splitting equivalent errors between `400` and `422` without a clear policy.

---

## 9. Pagination, Filtering, and Sorting

### 9.1 Pagination

List endpoints support page-number pagination.

Default page size: `25`
Maximum page size: `100`

Example:

```http
GET /api/v1/products/?page=2&page_size=50
```

Invalid page sizes must be rejected or safely normalized according to one documented policy.

The initial implementation uses one consistent behavior across list endpoints.

### 9.2 Filtering

Endpoints support filters relevant to their resource.

Examples:

```http
GET /api/v1/products/?is_active=true
GET /api/v1/inventory/balances/?warehouse_id={uuid}
GET /api/v1/orders/?status=confirmed
GET /api/v1/purchase-orders/?supplier_id={uuid}
```

Supported filters must be documented per endpoint.

Reject unsupported filter parameters instead of silently changing the meaning of a request. The implementation must adopt a consistent policy for rejecting unsupported parameters.

### 9.3 Search

Where defined, list endpoints support a `search` parameter.

Example:

```http
GET /api/v1/products/?search=rice
```

Search must be restricted to explicitly supported fields and must respect authorization and warehouse scope.

### 9.4 Sorting

Use an `ordering` parameter with an allowlist of supported fields.

Example:

```http
GET /api/v1/products/?ordering=name
GET /api/v1/products/?ordering=-created_at
```

A leading `-` means descending order.

Give every paginated query deterministic ordering, including a stable tie-breaker such as the resource ID, so records do not unpredictably move between pages when primary sort values match.

---

## 10. Concurrency and Idempotency

Inventory and fulfilment requests may be retried because of timeouts, network failures, or repeated user actions.

depotledger must distinguish safe retries from new business operations.

### 10.1 Idempotency keys

Operations that create business effects and may be retried must support idempotency.

The request header is:

```http
Idempotency-Key: 7b2d0b7e-0e3a-4bb6-8c10-4e3e8d5f4b11
```

Initially, require it for external order creation and other designated high-impact operations.

The server must associate the key with the authenticated caller or integration client, operation, request fingerprint, and stored outcome.

Rules:

1. The same key and equivalent request must not repeat the business effect.
2. Reusing the key with a materially different request must return `409 Conflict`.
3. Concurrent requests using the same key must not create duplicates.
4. Failed requests must follow a documented policy for whether the result is retained or the operation can be retried.
5. Keys must have a documented retention period.
6. Idempotency must be enforced in persistent storage, not only in application memory.

### 10.2 Optimistic concurrency

Add a version field or equivalent conditional-update mechanism where concurrent edits to ordinary resources can overwrite one another.

Inventory operations require stronger safeguards: stock availability must be validated within the database transaction using row locks or an equivalent atomic conditional-update strategy.

### 10.3 Inventory conflicts

If an operation cannot proceed because the inventory state has changed, return `409 Conflict`.

Example:

```json
{
  "error": {
    "code": "insufficient_available_stock",
    "message": "The requested quantity cannot be allocated.",
    "details": {
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "warehouse_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "requested_qty": "20",
      "available_qty": "12"
    }
  }
}
```

Include stock quantities only when the caller is authorized to see them.

---

## 11. Resource Endpoints

The following endpoints define the initial API surface. They are a contract baseline; exact fields, filters, and workflow rules must be finalized in implementation-specific schemas.

### 11.1 Authentication and identity

| Method  | Endpoint        | Purpose                                                             |
| ------- | --------------- | ------------------------------------------------------------------- |
| `POST`  | `/auth/login/`  | Authenticate an internal user if session authentication is selected |
| `POST`  | `/auth/logout/` | End the current session                                             |
| `GET`   | `/auth/me/`     | Return the current user's profile and effective permissions         |
| `GET`   | `/users/`       | List users; authorized administrators only                          |
| `POST`  | `/users/`       | Create a user                                                       |
| `GET`   | `/users/{id}/`  | Retrieve a user                                                     |
| `PATCH` | `/users/{id}/`  | Update permitted user fields                                        |
| `GET`   | `/roles/`       | List roles                                                          |
| `GET`   | `/permissions/` | List assignable permissions, if exposed                             |

Authentication routes depend on the selected session or token mechanism. Define explicit security policies for password changes, account recovery, role assignment, and integration credential rotation before implementation.

### 11.2 Products and catalogue

| Method  | Endpoint            | Purpose                                           |
| ------- | ------------------- | ------------------------------------------------- |
| `GET`   | `/products/`        | List and filter products                          |
| `POST`  | `/products/`        | Create a product                                  |
| `GET`   | `/products/{id}/`   | Retrieve a product                                |
| `PATCH` | `/products/{id}/`   | Update permitted product fields                   |
| `GET`   | `/categories/`      | List product categories                           |
| `POST`  | `/categories/`      | Create a category                                 |
| `GET`   | `/barcodes/{code}/` | Resolve a barcode if this lookup route is adopted |

Deactivate products instead of deleting a product referenced by historical transactions.

#### Example: Create product

`POST /api/v1/products/`

```json
{
  "sku": "RICE-25KG",
  "name": "Rice, 25 kg",
  "description": "25 kg bag of rice",
  "category_id": "550e8400-e29b-41d4-a716-446655440000",
  "base_unit": "bag",
  "is_active": true
}
```

The server validates SKU uniqueness, referenced categories, required fields, and permitted values.

Successful response: `201 Created`.

### 11.3 Warehouses and storage locations

| Method  | Endpoint                      | Purpose                    |
| ------- | ----------------------------- | -------------------------- |
| `GET`   | `/warehouses/`                | List accessible warehouses |
| `POST`  | `/warehouses/`                | Create a warehouse         |
| `GET`   | `/warehouses/{id}/`           | Retrieve warehouse details |
| `PATCH` | `/warehouses/{id}/`           | Update permitted fields    |
| `GET`   | `/warehouses/{id}/locations/` | List storage locations     |
| `POST`  | `/warehouses/{id}/locations/` | Create a storage location  |
| `GET`   | `/locations/{id}/`            | Retrieve a location        |
| `PATCH` | `/locations/{id}/`            | Update permitted fields    |

Every warehouse-specific operation must check warehouse access. Validate explicitly before deactivating a warehouse with active inventory or outstanding operations.

### 11.4 Inventory

| Method | Endpoint                                | Purpose                                          |
| ------ | --------------------------------------- | ------------------------------------------------ |
| `GET`  | `/inventory/balances/`                  | Query current stock balances                     |
| `GET`  | `/inventory/movements/`                 | Query committed physical stock movements         |
| `GET`  | `/inventory/reservations/`              | Query reservations                               |
| `GET`  | `/inventory/reservations/{id}/`         | Retrieve reservation details                     |
| `POST` | `/inventory/reservations/{id}/release/` | Release an eligible reservation                  |
| `POST` | `/inventory/adjustments/`               | Submit an adjustment request                     |
| `POST` | `/inventory/adjustments/{id}/approve/`  | Approve an adjustment where approval is required |
| `POST` | `/inventory/adjustments/{id}/post/`     | Commit an authorized adjustment                  |

Combine or separate adjustment approval and posting according to permissions and business policy.

There must be no generic endpoint such as `PATCH /inventory/balances/{id}/` that permits arbitrary modification of `on_hand_qty` or `reserved_qty`.

#### Example: Query balances

`GET /api/v1/inventory/balances/?warehouse_id={uuid}&product_id={uuid}`

Example response:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "product_id": "550e8400-e29b-41d4-a716-446655440000",
      "warehouse_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "location_id": null,
      "stock_status": "sellable",
      "on_hand_qty": "100.000",
      "reserved_qty": "25.000",
      "available_qty": "75.000"
    }
  ]
}
```

`available_qty` is a derived value, not an independently editable quantity.

Return balances by warehouse and storage location. Use a null location only for documented warehouse-level aggregation.

### 11.5 Suppliers and procurement

| Method  | Endpoint                          | Purpose                                 |
| ------- | --------------------------------- | --------------------------------------- |
| `GET`   | `/suppliers/`                     | List suppliers                          |
| `POST`  | `/suppliers/`                     | Create a supplier                       |
| `GET`   | `/suppliers/{id}/`                | Retrieve supplier                       |
| `PATCH` | `/suppliers/{id}/`                | Update permitted fields                 |
| `GET`   | `/purchase-orders/`               | List purchase orders                    |
| `POST`  | `/purchase-orders/`               | Create a purchase order                 |
| `GET`   | `/purchase-orders/{id}/`          | Retrieve purchase order                 |
| `POST`  | `/purchase-orders/{id}/submit/`   | Submit a purchase order                 |
| `POST`  | `/purchase-orders/{id}/approve/`  | Approve a purchase order where required |
| `POST`  | `/purchase-orders/{id}/cancel/`   | Cancel an eligible purchase order       |
| `POST`  | `/purchase-orders/{id}/receipts/` | Record a goods receipt                  |
| `GET`   | `/goods-receipts/{id}/`           | Retrieve a goods receipt                |

Purchase orders and goods receipts must use explicit state transitions. A receipt records actual accepted, damaged, and rejected quantities and must not simply set stock to the ordered quantity.

#### Example: Create purchase order

`POST /api/v1/purchase-orders/`

```json
{
  "supplier_id": "550e8400-e29b-41d4-a716-446655440000",
  "warehouse_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "currency": "GHS",
  "lines": [
    {
      "product_id": "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "ordered_qty": "100.000",
      "unit_cost": "45.00"
    }
  ]
}
```

The server validates supplier, warehouse, products, currency, quantities, and permissions.

Successful response: `201 Created`.

### 11.6 Customers and sales orders

| Method  | Endpoint                             | Purpose                                    |
| ------- | ------------------------------------ | ------------------------------------------ |
| `GET`   | `/customers/`                        | List customers                             |
| `POST`  | `/customers/`                        | Create a customer                          |
| `GET`   | `/customers/{id}/`                   | Retrieve customer                          |
| `PATCH` | `/customers/{id}/`                   | Update permitted fields                    |
| `GET`   | `/orders/`                           | List sales orders                          |
| `POST`  | `/orders/`                           | Create a sales order                       |
| `GET`   | `/orders/{id}/`                      | Retrieve order and lines                   |
| `POST`  | `/orders/{id}/confirm/`              | Confirm an eligible order                  |
| `POST`  | `/orders/{id}/cancel/`               | Cancel eligible unfulfilled quantities     |
| `POST`  | `/orders/{id}/allocate/`             | Request or perform allocation under policy |
| `POST`  | `/orders/{id}/release-reservations/` | Release eligible reservations              |

Order creation must not be treated as proof that all requested quantities are available.

Backordered quantities and active allocations must be represented separately. Allocation behavior must follow the configured policy and must not permit stock overselling.

#### Example: Create sales order

`POST /api/v1/orders/`

```json
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "warehouse_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "currency": "GHS",
  "lines": [
    {
      "product_id": "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "ordered_qty": "100.000",
      "unit_price": "60.00"
    }
  ],
  "external_reference": "CUSTOMER-ORDER-1042"
}
```

The example represents an order request, not an instruction to reserve all quantities unconditionally.

The server determines allocations, backorders, and the initial order state according to business rules.

### 11.7 Picking, packing, shipments, and delivery

| Method | Endpoint                                     | Purpose                                                        |
| ------ | -------------------------------------------- | -------------------------------------------------------------- |
| `GET`  | `/pick-lists/`                               | List picking tasks                                             |
| `POST` | `/pick-lists/`                               | Create a pick list                                             |
| `GET`  | `/pick-lists/{id}/`                          | Retrieve pick list                                             |
| `POST` | `/pick-lists/{id}/start/`                    | Begin picking                                                  |
| `POST` | `/pick-lists/{id}/record-picks/`             | Record picked quantities                                       |
| `POST` | `/pick-lists/{id}/complete/`                 | Complete picking                                               |
| `GET`  | `/shipments/`                                | List shipments                                                 |
| `POST` | `/shipments/`                                | Create a shipment where permitted                              |
| `GET`  | `/shipments/{id}/`                           | Retrieve shipment                                              |
| `POST` | `/shipments/{id}/pack/`                      | Mark eligible quantities packed                                |
| `POST` | `/shipments/{id}/dispatch/`                  | Dispatch and commit the corresponding physical stock deduction |
| `POST` | `/shipments/{id}/deliver/`                   | Record delivery                                                |
| `POST` | `/shipments/{id}/record-delivery-exception/` | Record an authorized delivery exception                        |

Define the exact split between shipment creation, packing, and dispatch in the fulfilment workflow.

Picking and packing do not automatically deduct physical stock. Dispatch is the default physical stock deduction point.

The dispatch operation must be transactional and idempotent. A repeated dispatch request must not deduct the same stock twice.

### 11.8 Inter-warehouse transfers

| Method | Endpoint                    | Purpose                                  |
| ------ | --------------------------- | ---------------------------------------- |
| `GET`  | `/transfers/`               | List accessible transfers                |
| `POST` | `/transfers/`               | Create a transfer request                |
| `GET`  | `/transfers/{id}/`          | Retrieve transfer                        |
| `POST` | `/transfers/{id}/submit/`   | Submit a transfer                        |
| `POST` | `/transfers/{id}/approve/`  | Approve where required                   |
| `POST` | `/transfers/{id}/dispatch/` | Dispatch goods from the source warehouse |
| `POST` | `/transfers/{id}/receive/`  | Receive dispatched goods at destination  |
| `POST` | `/transfers/{id}/cancel/`   | Cancel an eligible transfer              |

Transfer dispatch and transfer receipt are distinct events.

Dispatched goods become in-transit stock and must not be available for sale at the destination until received and accepted according to policy.

The source and destination warehouse permissions must both be checked.

### 11.9 Returns

| Method | Endpoint                  | Purpose                           |
| ------ | ------------------------- | --------------------------------- |
| `GET`  | `/returns/`               | List returns                      |
| `POST` | `/returns/`               | Create a return request           |
| `GET`  | `/returns/{id}/`          | Retrieve return                   |
| `POST` | `/returns/{id}/receive/`  | Record returned goods received    |
| `POST` | `/returns/{id}/inspect/`  | Record inspection and disposition |
| `POST` | `/returns/{id}/complete/` | Complete an eligible return       |

Returned items must not automatically become sellable inventory. Their physical receipt and stock disposition must be recorded separately.

### 11.10 Audit and reporting

| Method | Endpoint                      | Purpose                      |
| ------ | ----------------------------- | ---------------------------- |
| `GET`  | `/audit-events/`              | Query permitted audit events |
| `GET`  | `/reports/inventory-summary/` | Inventory summary            |
| `GET`  | `/reports/stock-movements/`   | Stock movement report        |
| `GET`  | `/reports/order-fulfilment/`  | Order fulfilment report      |
| `GET`  | `/reports/purchase-orders/`   | Procurement report           |

Audit and reporting endpoints must enforce the appropriate permissions and warehouse scope.

Audit events must not be editable through ordinary API endpoints.

Define report filters, date ranges, export formats, and large-result handling per endpoint.

---

## 12. Resource State Transitions

State transitions must be exposed through explicit action endpoints rather than accepting arbitrary status changes.

Examples:

* `POST /orders/{id}/confirm/`
* `POST /purchase-orders/{id}/approve/`
* `POST /shipments/{id}/dispatch/`
* `POST /transfers/{id}/receive/`

The backend rejects illegal transitions.

For example, reject dispatch of a shipment when required picking or packing conditions are unmet, or if the corresponding inventory allocation is no longer valid.

An invalid transition returns `409 Conflict`.

Example:

```json
{
  "error": {
    "code": "invalid_state_transition",
    "message": "The shipment cannot be dispatched in its current state.",
    "details": {
      "current_state": "draft",
      "requested_operation": "dispatch"
    }
  }
}
```

Do not accept arbitrary client-supplied status changes such as:

```json
{
  "status": "dispatched"
}
```

when dispatch requires physical stock movements and additional business validation.

---

## 13. Monetary and Currency Rules

Sales orders and purchase orders must retain their transaction currency.

Monetary values must use decimal arithmetic. The server validates supported currencies, precision, and scale.

The API must distinguish between:

* Transaction currency.
* Company reporting currency.
* Exchange rate.
* The effective date or source of the exchange rate.

The initial release does not provide a complete accounting ledger or full inventory valuation system.

The backend calculates totals using documented rounding rules. Clients must not be trusted to provide authoritative totals.

A currency conversion must not be inferred merely because two monetary values appear in the same report.

---

## 14. Asynchronous Operations and Webhooks

Some operations may take longer than a normal HTTP request, particularly report generation and external event delivery.

Where an operation is genuinely asynchronous, return `202 Accepted` with an identifier that can be used to query its status.

Example:

```json
{
  "operation_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "status_url": "/api/v1/operations/550e8400-e29b-41d4-a716-446655440000/"
}
```

Implement the operations-status endpoint before using this response pattern.

### 14.1 Webhooks

Define the following for outbound webhooks:

* Event types and payload schemas.
* Signature verification.
* Delivery retry policy.
* Timeouts and failure handling.
* Duplicate delivery behavior.
* Delivery history.
* Credential rotation.
* Event ordering guarantees, if any.

Webhook consumers must tolerate duplicate delivery.

The system persists important events through a transactional outbox so a committed business change is not lost merely because an external endpoint is unavailable.

---

## 15. External API Integration

External clients must use the same business rules as internal users.

The integration API must not offer a shortcut around inventory reservations, order validation, permissions, or audit requirements.

External clients must have:

* Individually managed credentials.
* Explicitly granted permissions or scopes.
* Documented request and response schemas.
* Rate limits.
* Idempotency support for designated write operations.
* A documented policy for deactivation and credential revocation.

Where external systems submit their own order references, preserve the external reference and enforce uniqueness within the relevant integration scope when required.

Define whether an external order creates a draft, confirmed order, or order awaiting review. Never infer that decision from authentication alone.

---

## 16. Audit Requirements

Sensitive operations must create audit records.

Examples include:

* User and permission changes.
* Product and warehouse configuration changes.
* Inventory adjustments.
* Reservation release and manual allocation.
* Order cancellation.
* Shipment dispatch.
* Transfer dispatch and receipt.
* Integration credential creation, rotation, and revocation.

Where appropriate, audit records must identify:

* The actor.
* The action.
* The affected resource.
* The timestamp.
* The request identifier.
* Relevant before-and-after values or a safe change summary.
* The reason supplied for sensitive manual operations.

Secrets, passwords, authentication tokens, and unnecessary personal data must never be copied into audit payloads.

---

## 17. OpenAPI Contract

The API must have a machine-readable OpenAPI specification.

The contract documents:

* Endpoint paths and HTTP methods.
* Authentication schemes.
* Request schemas.
* Response schemas.
* Error codes.
* Pagination and filters.
* Idempotency headers.
* State transitions.
* Permissions and warehouse-scope requirements.

The implementation generates and exposes the OpenAPI document through a documented development endpoint and provide a way to validate that the contract matches the implemented API.

Generate frontend types from the contract, reducing drift between backend and frontend definitions.

---

## 18. API Testing Requirements

The following must be covered by automated tests.

### General API behavior

* Correct status codes.
* Consistent error envelope.
* Pagination and filtering.
* UUID and decimal validation.
* Authentication failures.
* Permission enforcement.
* Warehouse-scope enforcement.

### Inventory

* Balance endpoints cannot be used to mutate stock.
* Reservation operations preserve quantity invariants.
* Concurrent allocations cannot oversell stock.
* Dispatch records physical stock changes exactly once.
* Transfer receipt does not occur before eligible dispatch.
* Adjustments require the appropriate permissions and state transitions.

### Idempotency

* A repeated request with the same key does not repeat its business effect.
* A conflicting payload with the same key is rejected.
* Concurrent duplicate requests do not create duplicate records or movements.
* Failure and retry behavior matches the documented policy.

### Business workflows

* Purchase order receiving updates inventory through Inventory-owned operations.
* Sales order cancellation releases or adjusts eligible reservations correctly.
* Partial fulfilment preserves outstanding quantities.
* Returned goods are classified before becoming available for sale.
* External clients cannot access unauthorized warehouses or resources.

---

## 19. Implementation Rules

The following rules are mandatory for the initial implementation:

1. API views and serializers must not become the sole home of business logic.
2. Domain services must own important state transitions.
3. Inventory changes must use Inventory-owned services.
4. Multi-record business operations must use database transactions.
5. Inventory concurrency must be enforced at the database level.
6. High-impact retriable operations must implement idempotency where designated.
7. API errors must use stable machine-readable codes.
8. Protected operations must enforce permissions on the backend.
9. The OpenAPI contract must remain consistent with the implementation.
10. External integrations must not receive direct database access.
11. Audit and movement history must not be silently rewritten to correct past events.
12. API changes must include tests for their expected behavior.

---

## 20. Decisions Required Before Finalizing the Contract

Resolve the following items when their dependent implementation begins:

| Decision                         | Direction                                                          | Why it matters                               |
| -------------------------------- | -------------------------------------------------------------------- | -------------------------------------------- |
| Internal authentication          | Secure sessions for a first-party web app where deployment permits   | Determines login, CSRF, and session behavior |
| External authentication          | Individually managed integration credentials with scoped permissions | Defines the external trust boundary          |
| Inventory allocation granularity | Decide between warehouse-level and storage-location-level allocation | Affects balance schemas and picking          |
| Backorder allocation             | Automatic allocation or staff approval                               | Determines order and reservation workflows   |
| Reservation renewal              | Define whether expiry can be extended                                | Affects reservation endpoints and jobs       |
| Adjustment approval              | Require approval for sensitive or high-value adjustments             | Affects permissions and state transitions    |
| Over-receiving                   | Reject, allow within a threshold, or require approval                | Affects receiving validation                 |
| Idempotency retention            | Define duration and retry behavior                                   | Affects persistent storage and integrations  |
| API rate limits                  | Define defaults and per-client overrides                             | Affects external API operations              |
| Webhooks                         | Decide whether outbound events are in the initial release            | Affects integration scope                    |
| Reporting                        | Define initial report filters and export requirements                | Affects endpoints and query performance      |

Resolve these decisions when their dependent implementation begins. Do not guess them inside individual endpoint handlers.

---

## 21. Definition of API Readiness

The API contract is ready for initial implementation when:

* The common response and error formats are agreed upon.
* Authentication and authorization approaches are documented.
* Pagination and filtering conventions are defined.
* Core resource endpoints are identified.
* Inventory operations use explicit state transitions.
* Idempotency requirements are defined for critical write operations.
* Decimal and timestamp representations are consistent.
* OpenAPI is included in the development workflow.
* Tests are planned for permissions, concurrency, and duplicate requests.
* Unresolved business decisions are clearly tracked.

**Document status:** Draft baseline. Refine the exact request schemas, response schemas, permission matrix, and state-transition rules as the relevant modules are implemented.
