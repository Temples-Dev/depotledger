# depotledger — Security and Permissions

**Status:** Approved
**Version:** 1.0
**Scope:** Authentication, authorization, warehouse access, integration security, audit, and operational safeguards.

---

## 1. Purpose

This document defines the security architecture for depotledger, a multi-warehouse inventory and fulfilment platform.

The objectives are to:

* Prevent unauthorized access to business data and operations.
* Restrict staff to their assigned responsibilities and warehouses.
* Protect inventory from unauthorized or accidental modification.
* Secure external API integrations.
* Maintain accountability for sensitive actions.
* Reduce the risk of credential compromise and data exposure.
* Establish security requirements that can be tested automatically.

Security must be enforced by the backend. The frontend may adapt its interface to permissions, but it must never be treated as the security boundary.

## 2. Security Principles

depotledger follows these principles.

### 2.1 Deny by default

Every protected operation requires an explicit permission. Users do not gain access merely because they are authenticated.

### 2.2 Least privilege

Users and integration clients receive only the permissions needed for their responsibilities.

### 2.3 Separation of duties

Sensitive operations may require separate permissions for requesting, approving, and executing them.

For example, a user who requests a high-impact inventory adjustment must not automatically be allowed to approve it.

### 2.4 Warehouse-scoped access

Access to one warehouse does not automatically grant access to every warehouse.

### 2.5 Backend enforcement

Every protected request must be authorized on the server, including requests made directly to the API.

### 2.6 Traceability

Sensitive operations must produce audit records that identify the actor, action, affected resource, and outcome.

### 2.7 Secure failure

Authorization failures and unexpected errors must not expose credentials, internal implementation details, or protected data.

### 2.8 Explicit trust boundaries

Internal users, external integration clients, background workers, and administrative processes have distinct identities and privileges.

---

## 3. Identity Types

depotledger recognizes four categories of actors.

| Actor                | Description                                                    | Authentication                                                                     |
| -------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Internal user        | Staff using the web application                                | User authentication                                                                |
| Integration client   | An external system calling the API                             | Client credentials or another explicitly approved machine-authentication mechanism |
| Background worker    | A process executing scheduled or asynchronous work             | Restricted service identity                                                        |
| System administrator | An authorized operator responsible for platform administration | Strongly protected administrative identity                                         |

A person holds multiple business permissions through one human account. Never reuse a human account as an integration credential.

Background jobs must execute under a defined service identity or an explicitly recorded initiating actor and service identity. They must not automatically inherit unrestricted administrative privileges.

## 4. Authentication

### 4.1 Internal users

For the first-party React application, secure server-managed sessions are the preferred default when the deployment architecture permits them.

Requirements:

* Store session identifiers in `HttpOnly` cookies.
* Use `Secure` cookies in production.
* Configure `SameSite` appropriately for the deployment.
* Apply CSRF protection to unsafe cookie-authenticated requests.
* Use HTTPS in deployed environments.
* Expire sessions according to a documented policy.
* Invalidate sessions on logout and relevant security events.
* Protect password reset and account recovery workflows.
* Rate-limit login and recovery attempts.

If a token-based mechanism is selected instead, its issuance, expiration, revocation, and storage behavior must be documented before implementation.

### 4.2 Integration clients

Each external integration must have its own client identity and credentials.

Requirements:

* Credentials must be generated securely.
* Secrets must not be committed to source control.
* Credentials must not be included in URLs.
* Secrets must be stored and displayed according to a secure credential-management policy.
* Credential rotation and revocation must be supported.
* Each client must have explicit permissions and warehouse scope.
* Authentication failures must not reveal whether a secret or client identifier was the incorrect component.

A shared credential used by multiple unrelated integrations is prohibited because it prevents reliable attribution and makes revocation unnecessarily disruptive.

### 4.3 Administrative accounts

Administrative access must be restricted to designated users.

Require stronger authentication for privileged accounts, including multi-factor authentication where the deployment supports it.

Administrative credentials must not be shared between people.

### 4.4 Background workers

Background workers must receive only the access required for their assigned jobs.

A notification worker, for example, must not receive unrestricted permission to create users or perform inventory adjustments.

---

## 5. Authorization Model

depotledger uses **role-based access control (RBAC)** combined with resource and warehouse-scope checks.

RBAC answers:

> Is this actor allowed to perform this type of operation?

Scope checks answer:

> Is this actor allowed to perform it on this particular resource or warehouse?

Apply both checks to every scoped operation.

### 5.1 Authorization decision

A protected operation must be permitted only when all applicable conditions are satisfied:

1. The actor is authenticated.
2. The actor's account or integration is active.
3. The actor has the required permission.
4. The actor is authorized for the relevant warehouse and resource.
5. The resource is in a state that permits the operation.
6. Any required approval or separation-of-duties rule is satisfied.

Passing a permission check does not override a business rule or invalid state transition.

### 5.2 Permission structure

Permissions use stable machine-readable identifiers.

Examples:

```text
catalogue.products.read
catalogue.products.create
catalogue.products.update

warehousing.warehouses.read
warehousing.warehouses.manage

inventory.balances.read
inventory.movements.read
inventory.reservations.read
inventory.reservations.release
inventory.adjustments.create
inventory.adjustments.approve
inventory.adjustments.post

procurement.purchase_orders.read
procurement.purchase_orders.create
procurement.purchase_orders.approve
procurement.receipts.post

sales.orders.read
sales.orders.create
sales.orders.cancel
sales.orders.allocate

fulfilment.picking.manage
fulfilment.shipments.dispatch
fulfilment.shipments.deliver

transfers.create
transfers.approve
transfers.dispatch
transfers.receive

identity.users.read
identity.users.manage
identity.roles.manage

audit.events.read
reports.inventory.read
integrations.clients.manage
```

These identifiers are conventions. The final permission catalogue must be centrally defined and validated rather than scattered as arbitrary strings throughout the codebase.

---

## 6. Initial Role Definitions

Roles are collections of permissions. Apply the following roles as the initial set. Extend them without treating job titles as fixed.

### 6.1 System Administrator

Responsible for platform configuration and administrative access.

Typical permissions:

* Manage users and role assignments.
* Manage platform-level configuration.
* Manage integration clients and credentials.
* View permitted audit and operational records.
* Configure warehouse access.

A system administrator must not automatically bypass inventory invariants or business approval rules. Administrative access is not permission to alter historical movements.

### 6.2 Inventory Manager

Responsible for inventory oversight.

Typical permissions:

* Read stock balances and movement history.
* Review reservations and backorders.
* Create and review adjustments.
* Approve adjustments where authorized.
* Access inventory reports.
* Review inventory discrepancies.

Posting adjustments remains subject to the configured approval and separation-of-duties policy.

### 6.3 Warehouse Operator

Responsible for daily warehouse operations.

Typical permissions:

* Read stock balances for assigned warehouses.
* Record receiving activities where permitted.
* Perform picking and packing.
* Dispatch authorized shipments.
* Dispatch and receive authorized transfers.
* Record permitted operational exceptions.

Warehouse operators must not automatically receive permission to manage users, integration credentials, or company-wide configuration.

### 6.4 Procurement Officer

Responsible for purchasing and supplier operations.

Typical permissions:

* Read and manage supplier records.
* Create and manage purchase orders.
* Submit purchase orders for approval.
* View goods receipts.
* Record receipts where the business workflow permits.

Approval authority must be granted separately where procurement separation of duties is required.

### 6.5 Sales Officer

Responsible for customer orders.

Typical permissions:

* Read customer records.
* Create and manage sales orders.
* View order status and fulfilment progress.
* Request cancellation of eligible orders.
* View permitted inventory availability.

This role must not be allowed to modify physical stock balances directly.

### 6.6 Fulfilment Officer

Responsible for order fulfilment.

Typical permissions:

* View confirmed orders ready for fulfilment.
* Manage pick lists.
* Record picking and packing.
* Prepare shipments.
* Dispatch shipments if granted the dispatch permission.
* Record delivery status.

### 6.7 Auditor / Read-only Analyst

Responsible for oversight and reporting.

Typical permissions:

* Read authorized inventory records.
* Read movement history.
* Read audit events.
* Access approved reports.

This role must not modify inventory, orders, permissions, or audit history.

### 6.8 Integration Client

A non-human identity used by an external application.

Its permissions are assigned individually. It must not automatically inherit a broad internal staff role.

### 6.9 Role customization

The platform must allow authorized administrators to manage role assignments. Custom roles may be introduced if they remain within the permission catalogue and cannot grant permissions beyond the administrator's authority.

Do not hardcode business authorization as role-name comparisons.

Prefer permission checks such as:

```python
user.has_perm("inventory.adjustments.approve")
```

over:

```python
if user.role == "inventory_manager":
    ...
```

Base business logic on permissions, not on fragile role-name checks, regardless of the Django implementation detail.

---

## 7. Permission Matrix

This matrix establishes the initial intended access pattern. It must be converted into explicit automated authorization tests before marking the corresponding features complete.

| Operation                  | System Admin       | Inventory Manager | Warehouse Operator             | Procurement Officer            | Sales Officer            | Auditor   |
| -------------------------- | ------------------ | ----------------- | ------------------------------ | ------------------------------ | ------------------------ | --------- |
| Read products              | Yes                | Yes               | Yes                            | Yes                            | Yes                      | Yes       |
| Manage products            | Yes                | Limited by grants | No                             | No                             | No                       | No        |
| Read assigned stock        | If scoped          | Yes               | Yes                            | As needed                      | Availability only        | If scoped |
| Read movement history      | If scoped          | Yes               | If granted                     | Receipt-related                | No by default            | If scoped |
| Create adjustments         | If granted         | Yes               | If granted                     | No                             | No                       | No        |
| Approve adjustments        | If granted         | Yes               | No by default                  | No                             | No                       | No        |
| Post adjustments           | If granted         | If granted        | No by default                  | No                             | No                       | No        |
| Create purchase orders     | If granted         | No by default     | No                             | Yes                            | No                       | No        |
| Approve purchase orders    | If granted         | No by default     | No                             | Separate grant                 | No                       | No        |
| Record goods receipts      | If granted         | If granted        | If granted                     | If granted                     | No                       | No        |
| Create sales orders        | If granted         | No by default     | No                             | No                             | Yes                      | No        |
| Manage picking and packing | If granted         | If granted        | Yes                            | No                             | No                       | No        |
| Dispatch shipments         | If granted         | If granted        | If granted                     | No                             | No                       | No        |
| Dispatch transfers         | If granted         | If granted        | If granted                     | No                             | No                       | No        |
| Receive transfers          | If granted         | If granted        | If granted                     | No                             | No                       | No        |
| Manage users and roles     | Yes, within policy | No                | No                             | No                             | No                       | No        |
| Manage integration clients | Yes, within policy | No                | No                             | No                             | No                       | No        |
| Read audit events          | If granted         | Inventory-related | No by default                  | No by default                  | No by default            | Yes       |
| Read reports               | If granted         | Inventory reports | Operational reports if granted | Procurement reports if granted | Sales reports if granted | If scoped |

**Important:** “System Admin: Yes” means the operation may be granted to an administrator within the defined security policy. It does not permit bypassing transaction rules, warehouse restrictions, or mandatory approvals.

The final matrix must specify each permission precisely, including whether access is company-wide, warehouse-scoped, or restricted to records owned by a user or integration.

---

## 8. Warehouse Access Control

Warehouse access is a separate dimension of authorization.

### 8.1 Warehouse assignments

Users may be assigned access to one or more warehouses.

The relationship is:

```text
User
 └── UserWarehouseAccess
      ├── user_id
      ├── warehouse_id
      ├── access_level or scoped permissions
      └── is_active
```

Represent access through a normalized set of grants. Do not store duplicate or conflicting representations of the same authorization decision.

### 8.2 Warehouse selection

The frontend allows a user to select their active warehouse.

However, selecting a warehouse does not grant access to it. The backend must validate every warehouse identifier supplied in a request.

The active warehouse is a user-interface convenience, not a security boundary.

### 8.3 Multi-warehouse operations

Some operations span multiple warehouses, particularly transfers.

A transfer from Warehouse A to Warehouse B must validate the relevant source and destination permissions.

Permissions may distinguish between:

* Creating a transfer.
* Approving a transfer.
* Dispatching from the source.
* Receiving at the destination.

### 8.4 Company-wide views

Company-wide reports and cross-warehouse inventory queries require explicit permissions.

A user assigned to one warehouse must not be able to bypass scope restrictions by omitting the warehouse filter or querying a report endpoint.

### 8.5 Scope enforcement

Warehouse scope must be enforced in the backend query and service layers.

Do not fetch all records and rely on the frontend to hide unauthorized rows.

---

## 9. Separation of Duties

Sensitive workflows may require distinct actors for request, approval, and execution.

### 9.1 Inventory adjustments

The workflow is:

1. An authorized user creates an adjustment request.
2. The request records the affected stock, quantity difference, and reason.
3. An authorized approver reviews the request.
4. An authorized operation posts the adjustment.
5. The system records the physical stock movement and audit event transactionally.

For sensitive adjustments, the requester must not approve their own request.

Define whether all adjustments require approval or only adjustments exceeding a configured threshold or risk category.

### 9.2 Purchase orders

Purchase-order approval must be controlled independently from purchase-order creation where business policy requires it.

Implement approval rules explicitly from order value, supplier, or policy. Never infer them from frontend behavior.

### 9.3 Dispatch and receipt

Transfer dispatch and receipt must remain distinct operations. The system must not allow a user to mark an undelivered transfer as received simply by changing its status.

### 9.4 Privileged overrides

If emergency administrative overrides are introduced, they must be narrowly defined, explicitly authorized, auditable, and incapable of corrupting inventory history.

No override may disable essential transactional integrity or create arbitrary stock balance changes.

---

## 10. External Integration Security

External clients are independent security principals.

### 10.1 Client configuration

Give each client:

* A unique identifier.
* A securely managed credential.
* An active or revoked status.
* An assigned permission set.
* Optional warehouse scope.
* Rate-limit configuration.
* Creation and last-used timestamps.
* Credential rotation and revocation history where appropriate.

Never store a recoverable plaintext copy of a secret after issuance. Verify secrets through the selected authentication scheme or secret-management mechanism.

### 10.2 Scope examples

Example integration permissions:

```text
integration.orders.create
integration.orders.read
integration.products.read
integration.inventory.availability.read
```

An integration that only submits orders must not automatically receive permissions to:

* Read full inventory movement history.
* Modify products.
* Manage users.
* Approve adjustments.
* Dispatch shipments.
* Create other integration clients.

### 10.3 External order submission

External orders must pass through the same sales and inventory domain services as internal orders.

The API must validate:

* Client identity and permission.
* Customer or account mapping.
* Warehouse scope.
* Product identifiers and quantities.
* Request idempotency.
* Applicable order policies.

External references must be retained so orders can be traced to their originating systems.

### 10.4 Credential lifecycle

The system must support:

* Issuing credentials.
* Rotating credentials.
* Revoking credentials.
* Disabling a compromised client.
* Auditing credential-management operations.

Revocation must take effect promptly and must not depend on a long-lived application cache expiring naturally.

### 10.5 Rate limiting

Configure rate limits per client and endpoint class.

Apply distinct limits to write operations, authentication endpoints, and resource-intensive reports.

Rate limiting is an operational safeguard, not a replacement for authentication or authorization.

---

## 11. Application Security

### 11.1 Input validation

All incoming data must be validated on the backend.

Validation includes:

* Field types and formats.
* Quantity and monetary precision.
* UUID validity.
* Referenced resource existence.
* Resource and warehouse permissions.
* Allowed state transitions.
* Business invariants.
* Payload size and collection limits.

Never trust client-provided totals, permissions, derived availability, or status transitions.

### 11.2 Mass assignment protection

Serializers must expose only fields clients are permitted to set.

Clients must not be able to assign protected fields such as:

* Internal approval state.
* Posted inventory quantities.
* Audit actor identifiers.
* Privilege assignments without the required permission.
* System-generated timestamps.
* Computed order totals.
* Internal reconciliation fields.

### 11.3 SQL and query safety

Use Django ORM or parameterized queries. Never interpolate untrusted input directly into SQL.

Filter and sorting fields must be explicitly allowlisted.

### 11.4 Cross-site request forgery

If cookie-based sessions are used, unsafe requests must be protected against CSRF.

CORS configuration must specify the intended frontend origins. Wildcard origins combined with credentialed requests must not be used as a shortcut.

### 11.5 Cross-site scripting

User-supplied strings must be rendered safely. Do not render untrusted HTML without an explicit, justified sanitization strategy.

### 11.6 Transport security

Production traffic must use HTTPS. Protect sensitive internal service communications according to the deployment environment.

### 11.7 Error handling

Public API responses must not reveal:

* Stack traces.
* SQL statements.
* Secret values.
* Session or authentication tokens.
* Internal filesystem paths.
* Unnecessary infrastructure details.

Expose detailed errors only through protected server-side logs.

---

## 12. Secrets and Configuration

Credentials and secret configuration must be kept outside source control.

Examples include:

* Database passwords.
* Django secret key.
* Session or token signing secrets.
* Integration credentials.
* Email or notification provider credentials.
* Production service credentials.

Use a local environment file excluded from version control for development.

Use a suitable secret-management mechanism in production.

Secret rotation must be possible without exposing secrets in logs or application responses.

Never use a production secret as a default development value.

---

## 13. Audit Logging

Audit records provide accountability for sensitive business and administrative actions.

### 13.1 Required audit events

At minimum, audit:

* Login failures and relevant account-security events.
* User creation, deactivation, and permission changes.
* Integration client creation, rotation, and revocation.
* Warehouse access assignment changes.
* Inventory adjustment creation, approval, and posting.
* Manual reservation release.
* Order cancellation.
* Shipment dispatch.
* Transfer dispatch and receipt.
* Relevant administrative configuration changes.

### 13.2 Audit event fields

An audit record contains:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "actor_type": "user",
  "actor_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "action": "inventory.adjustment.posted",
  "resource_type": "inventory_adjustment",
  "resource_id": "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "warehouse_id": "8ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "request_id": "9ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "occurred_at": "2026-10-09T09:30:00Z"
}
```

The implementation must use valid UUIDs and distinguish human actors from integration clients and background services.

Include a safe summary of changes and the reason for the action in audit events where the operation warrants it.

### 13.3 Audit integrity

Audit history must not be editable through ordinary application workflows.

Corrections to business data must be represented by new business events rather than silently rewriting the historical record.

The system must restrict audit access and establish a retention policy.

Audit logs are not a substitute for the inventory movement ledger: each serves a different purpose.

---

## 14. Security of Background Jobs

Background jobs must follow the same business authorization and integrity rules as synchronous operations.

Requirements:

* Validate the job's intended operation and payload.
* Use restricted service identities.
* Avoid storing credentials in job payloads.
* Treat task messages as potentially duplicated.
* Make retryable operations idempotent.
* Record the initiating actor.
* Log failures without exposing secrets.
* Ensure a revoked integration cannot continue initiating new privileged work through stale authorization state.

Define an explicit policy for jobs queued before a permission or credential revocation. Recheck authorization at execution time for high-impact operations.

---

## 15. Security Monitoring and Incident Response

The initial production system must provide enough operational visibility to detect suspicious activity and investigate failures.

Monitor for:

* Repeated authentication failures.
* Unusual API request volume.
* Repeated permission-denied responses.
* Unexpected changes in integration-client usage.
* Repeated failed inventory operations.
* Suspicious administrative activity.
* Background job failures and retry storms.
* Unusual patterns of inventory adjustments.

Logs include request identifiers and relevant actor/resource identifiers where safe.

Do not log passwords, authentication headers, session identifiers, API secrets, or complete sensitive payloads.

Define how compromised credentials are revoked, affected accounts are disabled, and relevant logs are preserved for investigation.

---

## 16. Data Protection

depotledger must collect and retain only the data needed for its business functions.

Requirements:

* Restrict access to customer and supplier contact information.
* Avoid including unnecessary personal data in logs.
* Establish retention rules for audit records and integration payloads.
* Protect database backups.
* Limit access to exported reports.
* Use secure transport and storage for backups.
* Test restoration procedures.
* Define a process for correcting inaccurate records without corrupting historical transactions.

Confirm data retention and deletion requirements against applicable business and legal obligations before production deployment.

---

## 17. Django Implementation Guidance

The implementation must centralize authorization policies and test them consistently.

Organization:

```text
apps/
├── identity/
│   ├── models.py
│   ├── permissions.py
│   ├── services.py
│   └── tests/
├── inventory/
│   ├── models.py
│   ├── permissions.py
│   ├── services.py
│   └── tests/
├── integrations/
│   ├── authentication.py
│   ├── permissions.py
│   ├── services.py
│   └── tests/
└── audit/
    ├── models.py
    ├── services.py
    └── tests/
```

Adjust this structure to the established repository.

Implementation requirements:

1. Define permissions centrally or through a consistent module-owned registry.
2. Apply authentication and permission classes to protected API views.
3. Filter querysets by authorized scope before returning records.
4. Check warehouse access in business operations as well as API entry points where needed.
5. Avoid using role names as the only authorization mechanism.
6. Use transactions for high-impact multi-record operations.
7. Record audit events reliably.
8. Ensure authorization checks cannot be bypassed through alternate endpoints.
9. Test unauthorized access using different users, roles, warehouses, and integration clients.
10. Keep security-sensitive behavior explicit and reviewable.

Combine Django's permission system, custom permission classes, and domain-level policy services.

---

## 18. Required Security Tests

### Authentication

* Unauthenticated users cannot access protected endpoints.
* Invalid credentials do not create a session.
* Logout invalidates the relevant session.
* Disabled users cannot continue performing protected operations.
* Session and CSRF controls behave as configured.

### Authorization

* Users without a required permission receive the correct denial.
* Users cannot assign permissions they are not authorized to manage.
* Users cannot change protected system fields through mass assignment.
* Read-only users cannot perform writes.
* A denied operation does not create partial business changes.

### Warehouse isolation

* A user assigned to Warehouse A cannot read Warehouse B's restricted inventory.
* A user cannot manipulate another warehouse's stock by changing an identifier.
* A transfer requires appropriate source and destination permissions.
* Reports cannot leak records from unauthorized warehouses.
* Omitted warehouse filters do not bypass authorization.

### Inventory integrity

* Unauthorized adjustments cannot be posted.
* Approval policies are enforced.
* Duplicate dispatch requests cannot deduct stock twice.
* Invalid reservation releases are rejected.
* Audit and movement records remain consistent with committed operations.

### Integration security

* Each client receives only its assigned permissions.
* Revoked credentials are rejected.
* One client's credentials cannot access another client's restricted scope.
* Rate limits are enforced.
* Repeated external order requests do not create duplicate orders.
* External clients cannot access administrative endpoints unless explicitly granted the necessary permission.

### Audit

* Sensitive actions create the required audit records.
* Audit events identify the correct actor.
* Audit records cannot be edited through normal API endpoints.
* Logs and audit payloads do not expose secrets.

---

## 19. Decisions Required

Confirm the following decisions before finalizing the affected features.

| Decision                       | Default                                                             |
| ------------------------------ | --------------------------------------------------------------------- |
| Internal authentication        | Secure server-managed sessions where deployment permits               |
| Privileged authentication      | Stronger authentication, including MFA where feasible                 |
| External client authentication | Individually managed credentials with explicit scopes                 |
| Role model                     | RBAC combined with warehouse and resource scope                       |
| Warehouse administrators       | May manage only the warehouse scope explicitly granted                |
| Adjustment approvals           | Separate request and approval permissions for sensitive adjustments   |
| Self-approval                  | Prohibited for workflows configured to require separation of duties   |
| Integration scope              | Per-client permissions and optional warehouse restrictions            |
| Audit access                   | Restricted to explicitly authorized roles                             |
| Credential revocation          | Prompt invalidation, including appropriate cache handling             |
| Audit retention                | Defined before production based on business and legal requirements    |
| Emergency overrides            | Not part of the initial release unless a concrete need is established |

---

## 20. Definition of Security Readiness

Security is ready for the first protected implementation milestone when:

* Authentication strategy is selected.
* The initial permission catalogue is defined.
* Initial roles are mapped to permissions.
* Warehouse-scoped authorization is designed.
* Integration-client isolation is documented.
* Sensitive operations and approval requirements are identified.
* Audit requirements are defined.
* Secrets and environment configuration have a documented handling policy.
* Security tests are included in the development workflow.
* Unauthorized requests are rejected without partial business effects.

**Document status:** Initial security baseline. Update this document when permissions, authentication mechanisms, or operational security requirements change. Any exception must be explicit, justified, and tested.
