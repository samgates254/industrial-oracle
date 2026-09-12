# Industrial Oracle - Backend Platform

Production-oriented backend for **Industrial Oracle**, an industrial operations intelligence, optimization, and decision-support platform.

Built with **Python 3.11**, **FastAPI**, **PostgreSQL**, **Redis**, **SQLAlchemy 2.x**, **Alembic**, **Pydantic**, and **pytest**, structured as a **Modular Monolith** with Clean Architecture, strict multi-tenant isolation, and an event-driven internal core.

---

## Architecture Overview

```
apps/
  api/          # FastAPI HTTP application, security dependencies, and middleware
  worker/       # Asynchronous background outbox worker process
  scheduler/    # Recurring cron job scheduler

src/industrial_oracle/
  core/         # Config, Database, Redis, Logging, Exceptions, Security (JWT & RBAC)
  shared/       # Generic repositories, Domain events, Event bus
  identity/     # Authentication, Users, RBAC
  organization/ # Organization, Memberships, Sites, Plants
  assets/       # Equipment, Assets, Machines, Production Lines, Telemetry Points
  operations/   # Work Orders, Production Runs, Material Consumption Traceability
  inventory/    # Items, Locations, Balances, Atomic Transactions
  maintenance/  # Maintenance Work Orders, Equipment State Coordination
  integrations/ # Transactional Outbox, Canonical Envelopes, Webhooks, Adapters
  energy/       # Energy Meters, Tariffs, Power Quality
  telemetry/    # Real-time metrics, Sampling, Anomaly thresholds
  optimization/ # MILP Solvers, Scenarios, Constraints, Runs
  audit/        # Immutable audit log system

migrations/     # Alembic database migration revisions
tests/          # Unit, Integration, Contract, Security, and E2E test suites
docker/         # Dockerfiles and Docker Compose orchestration
```

---

## Quickstart Guide

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (or via Docker)
- Redis 7 (or via Docker)

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Local Development with Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

### 3. Database Migrations
Apply all migrations to head:
```bash
alembic upgrade head
```

### 4. Running Tests
Run the complete automated test suite (216 tests across 47 test modules):
```bash
pytest -v
```

---

## Integration, Outbox & Event Infrastructure (Phase 5)

Phase 5 establishes a reliable integration and messaging backbone within the modular monolith:

1. **Transactional Outbox (`outbox_events`)**:
   - Atomic business state mutation + domain event persistence in a single transactional unit of work.
   - Statuses: `PENDING`, `PROCESSING`, `PUBLISHED`, `FAILED`.
   - Concurrency protection: atomic batch claiming with lease expiration (`locked_by`, `lock_expires_at`) for automatic crashed-worker recovery.

2. **Canonical Event Envelope & Versioning**:
   - Technology-independent canonical envelope schema (`event_id`, `event_type`, `event_version`, `occurred_at`, `organization_id`, `aggregate_type`, `aggregate_id`, `correlation_id`, `causation_id`, `payload`).
   - Standardized versioning (`WorkOrderCompleted.v1`, `InventoryIssued.v1`, etc.).

3. **Background Outbox Worker (`apps/worker/`)**:
   - Polling engine with configurable batch size and lease durations.
   - Controlled exponential backoff retry policy (configurable max attempts).
   - Dead-letter retention: exhausted events transition to `FAILED` with complete diagnostic error evidence.
   - Administrative event replay endpoint: `POST /api/v1/integration/outbox/{id}/retry`.

4. **Idempotent Consumption Ledger (`event_consumptions`)**:
   - Enforces exactly-once side-effect execution using `(consumer_name, event_id)` uniqueness.
   - Safe deduplication when events are redelivered.

5. **Outbound Webhooks Foundation (`webhook_endpoints`)**:
   - Tenant-scoped webhook management with event pattern filtering (`WorkOrder*.v1`, etc.).
   - Secure HMAC-SHA256 signature generation (`X-Industrial-Oracle-Signature`).
   - Secret masking in all API representations (`whsec_****`).

---

## Implementation Roadmap

- [x] **Phase 1: Foundation** (Repository skeleton, configuration, database schema & migrations, logging, exceptions, API framework)
- [x] **Phase 2: Identity & Organization** (JWT authentication, RBAC, organization hierarchy, strict multi-tenancy, cross-tenant attack rejection)
- [x] **Phase 3: Assets & Hierarchy** (Plants, production lines, machines, asset registry, operational status state machines, telemetry binding)
- [x] **Phase 4: Operations & Supply Chain** (Work orders, production runs, maintenance execution, inventory ledger, material consumption)
- [x] **Phase 5: Event & Integration Infrastructure** (Transactional outbox, canonical event envelope, background worker, retries, idempotency, webhooks, audit replay)
- [ ] **Phase 6: Optimization Engine** (MILP formulation, async background worker, solver integration)
- [ ] **Phase 7: Telemetry & Energy** (Time-series sampling, energy meters, peak shaving)
- [ ] **Phase 8: Operational Decision Support & AI** (Recommendation engines, simulation models)
