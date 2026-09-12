# INDUSTRIAL ORACLE - ARCHITECTURAL BLUEPRINT

## 1. Executive Summary & Vision

**Industrial Oracle** is an enterprise-grade industrial operations intelligence, optimization, and decision-support platform. It is engineered for industrial facilities—including processing plants, discrete manufacturing, assembly lines, energy utilities, and logistics networks—providing real-time telemetry ingestion, predictive asset maintenance, dynamic inventory control, energy monitoring, and mixed-integer linear programming (MILP) operational scheduling.

### Architecture Choice: Modular Monolith
To ensure rapid evolution without the operational overhead, network latency, and eventual consistency traps of distributed microservices, Industrial Oracle is architected as a **Modular Monolith**:
- Single unified deployable codebase.
- Strict bounded contexts with explicit domain boundaries.
- No direct cross-domain database queries; interaction occurs via Application layer interfaces or Domain Events.
- CQRS applied selectively for high-throughput reads and heavy analytical queries.
- Clean Architecture layers enforced within every domain: `domain/`, `application/`, `infrastructure/`, `api/`.
- Designed for future extraction into discrete microservices with zero structural rework.

---

## 2. Core Domain Hierarchy & Physical Modeling

Industrial Oracle models the physical and operational hierarchy according to ISA-95 standards:

```
Organization (Enterprise Tenant)
 └── Site (Geographic Facility / Industrial Park)
      └── Plant (Specific Processing or Manufacturing Facility)
           └── Production Line (Sequential Processing Chain)
                └── Machine / Asset (Physical Equipment, Sensors & Actuators)
```

### Entity Model Map:
1. **Organization**: The top-level multi-tenant boundary. Enforces strict logical isolation for all data, roles, and optimization runs.
2. **Site**: Physical compound or geographic site with address, timezone, and regional tariffs.
3. **Plant**: Distinct operational unit (e.g., Cement Mill, Assembly Facility, Chemical Refinery).
4. **Production Line**: Continuous or discrete line with rated throughput capacity per hour.
5. **Asset & Machine**: Physical machinery tagged with serial numbers, power ratings (kW), operating hours, and criticality indicators.
6. **Work Order**: Maintenance or operational tasks assigned to technicians, linked to assets and plants with strict state transitions.
7. **Production Run**: Scheduled execution batch producing a target volume of materials on a given production line.
8. **Material & Inventory**: SKU catalog, unit costs, on-hand balances, safety stock thresholds, and batch tracking.
9. **Maintenance Plan**: Preventive and condition-based maintenance triggers based on operating hours or elapsed calendar days.
10. **Energy Meter**: Submetering units attached to machines or plants measuring kWh consumption and power factor.
11. **Telemetry Point**: Time-series sampling point (vibration, temperature, pressure, RPM) with anomaly thresholds.
12. **Constraint & Scenario**: Mathematical declarations and what-if parameter sets for optimization runs.
13. **Optimization Run**: Asynchronous solver task evaluating objective functions subject to capacity and flow constraints.
14. **Alert**: Real-time operational or maintenance incidents classified by severity.
15. **Audit Log**: Immutable tamper-evident record of all state mutations.

---

## 3. Clean Architecture Within Each Domain

Each domain module under `src/industrial_oracle/<domain>/` strictly follows Clean Architecture:

```
<domain>/
 ├── domain/           # Pure business logic, invariants, value objects, domain events (No external dependencies)
 ├── application/      # Use cases, command handlers, query handlers, repository interfaces, DTOs
 ├── infrastructure/   # SQLAlchemy models, database repositories, Redis adapters, external APIs
 └── api/              # FastAPI routers, request/response schemas, transport validation
```

### Dependency Rules
1. **Domain Layer**: Independent of frameworks, databases, and third-party libraries. Depends only on Python primitives and `core.exceptions`.
2. **Application Layer**: Coordinates domain objects to execute use cases. Defines repository interfaces (`GenericRepository[T, ID]`).
3. **Infrastructure Layer**: Implements repository interfaces using SQLAlchemy 2.x and interacts with Redis and background brokers.
4. **API Layer**: Handles HTTP transport, OpenAPI schemas, serialization, and status codes. Never contains business logic.

---

## 4. Identity, Multi-Tenancy & RBAC Architecture (Phase 2)

### The Core Security Invariant
> **DATA BELONGING TO ORGANIZATION A MUST NEVER BE READABLE OR MUTABLE BY ORGANIZATION B.**

### Relational Model:
```
Organization
    │
    ├── Membership (role, is_active, status)
    │      │
    │      └── User (id, email, password_hash, is_active)
    │
    └── Tenant Resources (Sites, Plants, Lines, Assets, Audit Logs)
```
- A `User` can belong to multiple `Organization`s.
- `Membership` is the entity that determines a user's `Role` and status within a specific organization.
- Roles are **never** global properties of the `User`.

### Roles & Permissions Matrix:
| Role | Permissions Included | Purpose |
|---|---|---|
| **OWNER** | All 22 permissions | Enterprise administrative owner, billing, full tenant governance |
| **ADMIN** | `organization.*`, `users.*`, `assets.*`, `operations.*`, `maintenance.*`, `inventory.*`, `optimization.*`, `audit.read` | Site & facility operations administrator |
| **ENGINEER** | `organization.read`, `users.read`, `assets.*`, `operations.*`, `maintenance.*`, `inventory.read`, `optimization.*`, `audit.read` | Operational and asset engineering |
| **OPERATOR** | `organization.read`, `assets.read`, `operations.*` (read/create/update), `maintenance.*` (read/create/update), `inventory.*` (read/update) | Factory-floor equipment and work-order execution |
| **ANALYST** | `organization.read`, `assets.read`, `operations.read`, `maintenance.read`, `inventory.read`, `optimization.*`, `audit.read` | Performance analytics and scenario optimization |
| **VIEWER** | `organization.read`, `assets.read`, `operations.read`, `maintenance.read`, `inventory.read`, `optimization.read` | Read-only executive visibility |

### Reusable Authorization Dependencies:
- `require_role(*roles)`: Validates tenant context role.
- `require_permission(*permissions)`: Validates that all required permissions exist in the role's permission set.
- `get_tenant_context`: Derives tenant identity strictly from authenticated membership. Rejects client attempts to access organizations they do not actively belong to.

---

## 5. Security & Cryptography

1. **Password Hashing**: PBKDF2-HMAC-SHA256 with 100,000 rounds, 16-byte cryptographically secure random salt, constant-time verification.
2. **JWT Authentication**: RFC 7519 HS256 tokens with short expiration (60 minutes). Minimal claims (`sub`, `email`, `iat`, `exp`). Sensitive data and passwords are never exposed in JWTs or API responses.
3. **Audit Integration**: All administrative and identity lifecycle actions (`USER_CREATED`, `USER_UPDATED`, `USER_STATUS_CHANGED`, `USER_LOGIN`) trigger immutable audit log entries and internal domain events.

---

## 6. Observability & Standard Error Protocol

All API errors adhere to the standard envelope:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Asset with identifier 'AST-999' was not found.",
    "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "details": {}
  }
}
```
Probes:
- `GET /health`: Process liveness probe.
- `GET /ready`: Connectivity readiness probe checking PostgreSQL and Redis.

---

## 7. Operational Execution Architecture (Phase 4)

Phase 4 introduces the operational execution backbone connecting the physical enterprise model to real-world plant workflows.

### 1. Work Orders Architecture
- **Aggregate Root**: `WorkOrder` represents authorized directives for production, maintenance, repair, inspection, or setup.
- **State Machine**:
  ```text
  [DRAFT] ─── release() ───> [RELEASED] ─── start() ───> [IN_PROGRESS] ─── complete() ───> [COMPLETED]
     │                           │                             │
     │                           │                             ├── put_on_hold() ──> [ON_HOLD] ── resume() ──┐
     │                           │                             │                                            │
     │                           │                             └────────────────────────────────────────────┘
     └── cancel() ───────────────┴── cancel() ───────────────> [CANCELLED]
  ```
- **Concurrency & Invariants**:
  - `version` counter incremented on each transition for optimistic concurrency control.
  - Completed or Cancelled orders are terminal and immutable.
  - Domain events emitted: `WorkOrderCreated`, `WorkOrderReleased`, `WorkOrderStarted`, `WorkOrderPutOnHold`, `WorkOrderResumed`, `WorkOrderCompleted`, `WorkOrderCancelled`.

### 2. Production Runs Architecture
- **Aggregate Root**: `ProductionRun` tracks active shop-floor manufacturing against an authorized work order.
- **Quantity Invariants**:
  - `planned_quantity >= 0`, `actual_quantity >= 0`, `rejected_quantity >= 0`.
  - `rejected_quantity <= actual_quantity` (cannot reject more than total quantity produced).
- **State Machine**:
  - `PLANNED` ── start() ──> `RUNNING` ⇄ pause() / resume() ⇄ `PAUSED` ── complete() ──> `COMPLETED`.
  - Abort transition: `PLANNED` / `RUNNING` / `PAUSED` ── abort(reason) ──> `ABORTED`.
- **Domain Events**:
  - `ProductionRunCreated`, `ProductionRunStarted`, `ProductionRunPaused`, `ProductionRunResumed`, `ProductionQuantityRecorded`, `ProductionRunCompleted`, `ProductionRunAborted`.

### 3. Maintenance Execution & Machine Coordination
- **Aggregate Root**: `MaintenanceWorkOrder` built on top of the Work Order core.
- **Machine State Machine Coordination**:
  - Starting maintenance automatically transitions the referenced machine to `MAINTENANCE` status.
  - Completing maintenance restores the machine to `STOPPED` status.
  - Underlying work order lifecycle is synchronized.
- **Domain Events**: `MaintenanceStarted`, `MaintenanceCompleted`.

### 4. Inventory Foundation & Material Consumption
- **Entities**:
  - `Item`: Product SKU definition, UOM, and active status.
  - `InventoryLocation`: Storage bin, bay, or staging area scoped to site/plant.
  - `InventoryBalance`: Atomic balance with `version` tracking, non-negative available quantity enforcement.
  - `InventoryTransaction`: Immutable audit ledger recording `RECEIPT`, `ISSUE`, `ADJUSTMENT`, `RETURN`, `TRANSFER_IN`, `TRANSFER_OUT`.
  - `MaterialConsumption`: Links production runs and maintenance work orders to consumed inventory items with full traceability.

---

## 8. Integration, Transactional Outbox & Reliable Event Infrastructure (Phase 5)

Phase 5 establishes reliable integration and asynchronous event infrastructure, preventing data loss between business transactions and external systems.

### 1. The Outbox Pattern Architecture
```text
┌──────────────────────────────────────────────────────────┐
│               DATABASE TRANSACTION                       │
│                                                          │
│  1. Business State Mutation (WorkOrder, Run, Inventory) │
│  2. Audit Log Record                                     │
│  3. Outbox Event Persisted (outbox_events)               │
└────────────────────────────┬─────────────────────────────┘
                             │ Committed Atomically
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   OUTBOX WORKER                          │
│                                                          │
│  1. Claim Batch with Distributed Lease (lease_seconds)   │
│  2. Format into Canonical EventEnvelope                  │
│  3. Publish via IEventPublisher                          │
│  4. Handle Retries (Exponential Backoff)                 │
│  5. Mark PUBLISHED or Dead-Letter (FAILED)               │
└────────────────────────────┬─────────────────────────────┘
                             │ Dispatched
                             ▼
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │  Internal Consumers  │      │  Outbound Webhooks   │
   │  (Idempotent Ledger) │      │  (HMAC-SHA256 Signed)│
   └──────────────────────┘      └──────────────────────┘
```

### 2. Canonical Event Envelope Specification
Every event is standardized into a technology-agnostic envelope:
```json
{
  "event_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "event_type": "WorkOrderCompleted",
  "event_version": "v1",
  "qualified_event_type": "WorkOrderCompleted.v1",
  "occurred_at": "2026-09-12T19:30:00Z",
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "aggregate_type": "WorkOrder",
  "aggregate_id": "WO-100",
  "correlation_id": "req-98765",
  "causation_id": "cmd-12345",
  "payload": {
    "work_order_number": "WO-2026-001",
    "status": "COMPLETED"
  }
}
```

### 3. Outbox State Machine & Crash Recovery
- **Statuses**: `PENDING` → `PROCESSING` → `PUBLISHED` (or `FAILED` after max attempts).
- **Lease Timeout**: When an event is claimed, `lock_expires_at` is set. If a worker terminates or crashes before publishing, subsequent worker iterations reclaim the expired lease automatically.
- **Controlled Retries**: Deterministic exponential backoff calculation:
  $$\text{delay} = \text{base\_backoff} \times \text{multiplier}^{(\text{attempts} - 1)}$$
  Events exceeding `max_attempts` (default 3) transition to `FAILED` (dead-letter candidate) preserving complete diagnostic error logs.

### 4. Idempotent Consumption Ledger
- Table: `event_consumptions`
- Enforces unique constraint on `(consumer_name, event_id)`.
- If an event is redelivered due to network retransmissions, consumers detect prior consumption and skip side effects.

### 5. Outbound Webhook Security
- Webhook signing via HMAC-SHA256 with timestamp header `X-Industrial-Oracle-Signature`.
- Secrets are generated cryptographically and masked in all external API representations (`whsec_****`).
- Tenant isolation: Webhooks only trigger for events originating within the registering organization.
