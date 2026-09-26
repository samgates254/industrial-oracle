"""Repository implementations for Outbox, Event Consumption, and Webhook Endpoints.

Provides both high-performance PostgreSQL persistence (via SQLAlchemy AsyncSession)
and thread-safe in-memory fallbacks for unit tests.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid

from industrial_oracle.core.database import HAS_SQLALCHEMY, db_manager
from industrial_oracle.core.exceptions import EntityNotFoundException, BusinessRuleViolationException
from industrial_oracle.core.security import encrypt_secret, decrypt_secret
from industrial_oracle.integrations.application.interfaces import (
    IOutboxRepository,
    IEventConsumptionRepository,
    IWebhookRepository,
)
from industrial_oracle.integrations.domain.consumption import EventConsumption
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint
from industrial_oracle.integrations.infrastructure.models import (
    OutboxEventModel,
    EventConsumptionModel,
    WebhookEndpointModel,
)

if HAS_SQLALCHEMY:
    from sqlalchemy import and_, delete, func, or_, select, update
else:
    select = update = delete = and_ = or_ = func = None


# ==============================================================================
# 1. In-Memory Repository Implementations (For pure unit tests without database)
# ==============================================================================

class InMemoryOutboxRepository(IOutboxRepository):
    """Thread-safe in-memory outbox repository for testing and fallback."""

    def __init__(self) -> None:
        self._events: Dict[str, OutboxEvent] = {}
        self._lock = asyncio.Lock()

    async def append(self, outbox_event: OutboxEvent, session: Optional[Any] = None) -> OutboxEvent:
        async with self._lock:
            self._events[outbox_event.id] = outbox_event
            return outbox_event

    async def append_domain_event(
        self,
        domain_event: Any,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_version: str = "v1",
        session: Optional[Any] = None,
    ) -> OutboxEvent:
        """Converts domain event to outbox event and appends atomically."""
        outbox_event = OutboxEvent.from_domain_event(
            domain_event=domain_event,
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_version=event_version,
        )
        return await self.append(outbox_event, session=session)

    async def get_by_id(self, id: str, organization_id: Optional[str] = None) -> Optional[OutboxEvent]:
        async with self._lock:
            event = self._events.get(id)
            if not event:
                return None
            if organization_id and event.organization_id != str(organization_id):
                return None
            return event

    async def get_by_event_id(self, event_id: str, organization_id: Optional[str] = None) -> Optional[OutboxEvent]:
        async with self._lock:
            for ev in self._events.values():
                if ev.event_id == str(event_id):
                    if organization_id and ev.organization_id != str(organization_id):
                        return None
                    return ev
            return None

    async def claim_batch(
        self,
        batch_size: int,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> List[OutboxEvent]:
        async with self._lock:
            now = datetime.now(timezone.utc)
            claimable: List[OutboxEvent] = []

            all_eligible = []
            for ev in self._events.values():
                if ev.status == OutboxStatus.PENDING:
                    avail_time = datetime.fromisoformat(ev.available_at)
                    if avail_time <= now:
                        all_eligible.append(ev)
                elif ev.status == OutboxStatus.PROCESSING:
                    if ev.is_lock_expired(now):
                        all_eligible.append(ev)

            all_eligible.sort(key=lambda ev: ev.available_at)
            claimable = all_eligible[:batch_size]
            for ev in claimable:
                ev.mark_processing(worker_id=worker_id, lease_seconds=lease_seconds)

            return list(claimable)

    async def mark_published(self, id: str, processed_at: Optional[str] = None, session: Optional[Any] = None) -> None:
        async with self._lock:
            event = self._events.get(id)
            if event:
                event.mark_published(processed_at=processed_at)

    async def mark_failed(
        self,
        id: str,
        error: str,
        next_available_at: Optional[str] = None,
        max_attempts: int = 3,
        session: Optional[Any] = None,
    ) -> None:
        async with self._lock:
            event = self._events.get(id)
            if event:
                event.mark_failed(
                    error=error,
                    next_available_at=next_available_at,
                    max_attempts=max_attempts,
                )

    async def retry(self, id: str, organization_id: str) -> OutboxEvent:
        async with self._lock:
            event = await self.get_by_id(id, organization_id)
            if not event:
                raise EntityNotFoundException("Outbox event not found or does not belong to organization.")
            event.retry()
            return event

    async def count_pending(self, organization_id: Optional[str] = None) -> int:
        async with self._lock:
            count = 0
            for ev in self._events.values():
                if organization_id and ev.organization_id != str(organization_id):
                    continue
                if ev.status in (OutboxStatus.PENDING, OutboxStatus.PROCESSING):
                    count += 1
            return count

    async def count_failed(self, organization_id: Optional[str] = None) -> int:
        async with self._lock:
            count = 0
            for ev in self._events.values():
                if organization_id and ev.organization_id != str(organization_id):
                    continue
                if ev.status == OutboxStatus.FAILED:
                    count += 1
            return count

    async def get_oldest_pending_age_seconds(self, organization_id: Optional[str] = None) -> Optional[float]:
        async with self._lock:
            now = datetime.now(timezone.utc)
            oldest_age: Optional[float] = None

            for ev in self._events.values():
                if organization_id and ev.organization_id != str(organization_id):
                    continue
                if ev.status in (OutboxStatus.PENDING, OutboxStatus.PROCESSING):
                    ts_str = ev.occurred_at or ev.created_at
                    created = datetime.fromisoformat(ts_str)
                    age = (now - created).total_seconds()
                    if oldest_age is None or age > oldest_age:
                        oldest_age = age
            return oldest_age

    async def query_events(
        self,
        organization_id: str,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[OutboxEvent], int]:
        async with self._lock:
            filtered = [
                ev for ev in self._events.values()
                if ev.organization_id == str(organization_id)
            ]
            if event_type:
                filtered = [ev for ev in filtered if ev.event_type.startswith(event_type)]
            if aggregate_type:
                filtered = [ev for ev in filtered if ev.aggregate_type == aggregate_type]
            if aggregate_id:
                filtered = [ev for ev in filtered if ev.aggregate_id == str(aggregate_id)]
            if status:
                filtered = [ev for ev in filtered if ev.status == status or ev.status.value == status]
            if start_time:
                filtered = [ev for ev in filtered if ev.occurred_at >= start_time]
            if end_time:
                filtered = [ev for ev in filtered if ev.occurred_at <= end_time]

            filtered.sort(key=lambda ev: ev.occurred_at, reverse=True)
            total = len(filtered)
            paged = filtered[offset : offset + limit]
            return paged, total


class InMemoryEventConsumptionRepository(IEventConsumptionRepository):
    """In-memory idempotency consumption ledger."""

    def __init__(self) -> None:
        self._consumptions: Dict[Tuple[str, str], EventConsumption] = {}
        self._lock = asyncio.Lock()

    async def has_consumed(self, consumer_name: str, event_id: str, organization_id: Optional[str] = None) -> bool:
        async with self._lock:
            key = (consumer_name, str(event_id))
            rec = self._consumptions.get(key)
            if not rec:
                return False
            if organization_id and rec.organization_id and rec.organization_id != str(organization_id):
                return False
            return True

    async def record_consumption(self, consumption: EventConsumption, session: Optional[Any] = None) -> bool:
        async with self._lock:
            key = (consumption.consumer_name, str(consumption.event_id))
            if key in self._consumptions:
                return False  # Already consumed
            self._consumptions[key] = consumption
            return True

    async def get_consumption(self, consumer_name: str, event_id: str, organization_id: Optional[str] = None) -> Optional[EventConsumption]:
        async with self._lock:
            rec = self._consumptions.get((consumer_name, str(event_id)))
            if not rec:
                return None
            if organization_id and rec.organization_id and rec.organization_id != str(organization_id):
                return None
            return rec


class InMemoryWebhookRepository(IWebhookRepository):
    """In-memory webhook endpoints repository with encryption at rest simulation."""

    def __init__(self) -> None:
        self._webhooks: Dict[str, WebhookEndpoint] = {}
        self._encrypted_secrets: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def create(self, webhook: WebhookEndpoint, session: Optional[Any] = None) -> WebhookEndpoint:
        async with self._lock:
            # Encrypt secret at rest
            self._encrypted_secrets[webhook.id] = encrypt_secret(webhook.secret)
            self._webhooks[webhook.id] = webhook
            return webhook

    async def get_by_id(self, id: str, organization_id: Optional[str] = None, decrypt_secret_val: bool = False) -> Optional[WebhookEndpoint]:
        async with self._lock:
            wh = self._webhooks.get(id)
            if not wh:
                return None
            if organization_id and wh.organization_id != str(organization_id):
                return None
            sec = decrypt_secret(self._encrypted_secrets.get(id, wh.secret)) if decrypt_secret_val else wh.secret
            return WebhookEndpoint(
                id=wh.id,
                organization_id=wh.organization_id,
                name=wh.name,
                url=wh.url,
                secret=sec,
                active=wh.active,
                subscribed_event_types=wh.subscribed_event_types,
            )

    async def list_by_org(self, organization_id: str) -> List[WebhookEndpoint]:
        async with self._lock:
            return [wh for wh in self._webhooks.values() if wh.organization_id == str(organization_id)]

    async def update(self, webhook: WebhookEndpoint, session: Optional[Any] = None) -> WebhookEndpoint:
        async with self._lock:
            self._encrypted_secrets[webhook.id] = encrypt_secret(webhook.secret)
            self._webhooks[webhook.id] = webhook
            return webhook

    async def delete(self, id: str, organization_id: str, session: Optional[Any] = None) -> bool:
        async with self._lock:
            wh = self._webhooks.get(id)
            if not wh or wh.organization_id != str(organization_id):
                return False
            del self._webhooks[id]
            self._encrypted_secrets.pop(id, None)
            return True

    async def find_subscribers(self, organization_id: str, event_type: str, decrypt_secret_val: bool = True) -> List[WebhookEndpoint]:
        async with self._lock:
            subscribers: List[WebhookEndpoint] = []
            for wh in self._webhooks.values():
                if wh.organization_id == str(organization_id) and wh.matches_event(event_type):
                    sec = decrypt_secret(self._encrypted_secrets.get(wh.id, wh.secret)) if decrypt_secret_val else wh.secret
                    subscribers.append(
                        WebhookEndpoint(
                            id=wh.id,
                            organization_id=wh.organization_id,
                            name=wh.name,
                            url=wh.url,
                            secret=sec,
                            active=wh.active,
                            subscribed_event_types=wh.subscribed_event_types,
                        )
                    )
            return subscribers


# ==============================================================================
# 2. PostgreSQL Relational Repositories (Production & Integration Durability)
# ==============================================================================

class PostgresOutboxRepository(IOutboxRepository):
    """Production-grade PostgreSQL outbox repository adhering to transactional atomicity.

    Guarantees:
    1. Operates on the callers's active AsyncSession during atomic business mutations.
    2. Performs concurrent worker batch claiming using SELECT ... FOR UPDATE SKIP LOCKED.
    3. Two-phase worker claiming: Commits the PROCESSING lease to database before return.
    """

    def __init__(self, session: Optional[Any] = None) -> None:
        self._session = session

    def _to_entity(self, model: OutboxEventModel) -> OutboxEvent:
        return OutboxEvent(
            id=str(model.id),
            organization_id=str(model.organization_id),
            event_id=str(model.event_id),
            event_type=model.event_type,
            aggregate_type=model.aggregate_type,
            aggregate_id=str(model.aggregate_id),
            payload=model.payload if model.payload is not None else {},
            occurred_at=model.occurred_at.isoformat() if hasattr(model.occurred_at, "isoformat") else str(model.occurred_at),
            created_at=model.created_at.isoformat() if hasattr(model.created_at, "isoformat") else str(model.created_at),
            status=OutboxStatus(model.status) if hasattr(OutboxStatus, model.status) else model.status,
            attempts=model.attempts,
            available_at=model.available_at.isoformat() if hasattr(model.available_at, "isoformat") else str(model.available_at),
            processed_at=model.processed_at.isoformat() if model.processed_at and hasattr(model.processed_at, "isoformat") else None,
            last_error=model.last_error,
            correlation_id=model.correlation_id,
            causation_id=model.causation_id,
            version=model.version,
            locked_by=model.locked_by,
            lock_expires_at=model.lock_expires_at.isoformat() if model.lock_expires_at and hasattr(model.lock_expires_at, "isoformat") else None,
        )

    async def append(self, outbox_event: OutboxEvent, session: Optional[Any] = None) -> OutboxEvent:
        sess = session or self._session
        if not sess:
            raise RuntimeError("PostgresOutboxRepository.append requires an active database session.")

        uid = uuid.UUID(outbox_event.id) if isinstance(outbox_event.id, str) else outbox_event.id
        org_id = uuid.UUID(outbox_event.organization_id) if isinstance(outbox_event.organization_id, str) else outbox_event.organization_id
        ev_id = uuid.UUID(outbox_event.event_id) if isinstance(outbox_event.event_id, str) else outbox_event.event_id

        occurred_dt = datetime.fromisoformat(outbox_event.occurred_at) if isinstance(outbox_event.occurred_at, str) else (outbox_event.occurred_at or datetime.now(timezone.utc))
        avail_dt = datetime.fromisoformat(outbox_event.available_at) if isinstance(outbox_event.available_at, str) else (outbox_event.available_at or datetime.now(timezone.utc))

        model = OutboxEventModel(
            id=uid,
            organization_id=org_id,
            event_id=ev_id,
            event_type=outbox_event.event_type,
            aggregate_type=outbox_event.aggregate_type,
            aggregate_id=str(outbox_event.aggregate_id),
            payload=outbox_event.payload,
            occurred_at=occurred_dt,
            status=outbox_event.status.value if hasattr(outbox_event.status, "value") else str(outbox_event.status),
            attempts=outbox_event.attempts,
            available_at=avail_dt,
            correlation_id=outbox_event.correlation_id,
            causation_id=outbox_event.causation_id,
            version=outbox_event.version,
        )
        sess.add(model)
        return outbox_event

    async def append_domain_event(
        self,
        domain_event: Any,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_version: str = "v1",
        session: Optional[Any] = None,
    ) -> OutboxEvent:
        outbox_event = OutboxEvent.from_domain_event(
            domain_event=domain_event,
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_version=event_version,
        )
        return await self.append(outbox_event, session=session)

    async def get_by_id(self, id: str, organization_id: Optional[str] = None, session: Optional[Any] = None) -> Optional[OutboxEvent]:
        sess = session or self._session
        owns_sess = sess is None
        if owns_sess:
            sess = db_manager._sessionmaker()

        try:
            stmt = select(OutboxEventModel).where(OutboxEventModel.id == uuid.UUID(id))
            if organization_id:
                stmt = stmt.where(OutboxEventModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            m = res.scalar_one_or_none()
            return self._to_entity(m) if m else None
        finally:
            if owns_sess and hasattr(sess, "close"):
                await sess.close()

    async def get_by_event_id(self, event_id: str, organization_id: Optional[str] = None, session: Optional[Any] = None) -> Optional[OutboxEvent]:
        sess = session or self._session
        owns_sess = sess is None
        if owns_sess:
            sess = db_manager._sessionmaker()

        try:
            stmt = select(OutboxEventModel).where(OutboxEventModel.event_id == uuid.UUID(event_id))
            if organization_id:
                stmt = stmt.where(OutboxEventModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            m = res.scalar_one_or_none()
            return self._to_entity(m) if m else None
        finally:
            if owns_sess and hasattr(sess, "close"):
                await sess.close()

    async def claim_batch(
        self,
        batch_size: int,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> List[OutboxEvent]:
        """Atomically claims a batch using SELECT ... FOR UPDATE SKIP LOCKED and COMMITS the PROCESSING lease."""
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return []

        async with db_manager._sessionmaker() as sess:
            now = datetime.now(timezone.utc)
            lease_expires = now + timedelta(seconds=lease_seconds)

            stmt = (
                select(OutboxEventModel)
                .where(
                    or_(
                        and_(OutboxEventModel.status == "PENDING", OutboxEventModel.available_at <= now),
                        and_(OutboxEventModel.status == "PROCESSING", OutboxEventModel.lock_expires_at < now),
                    )
                )
                .order_by(OutboxEventModel.available_at.asc())
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )

            result = await sess.execute(stmt)
            models = result.scalars().all()

            if not models:
                return []

            claimed = []
            for m in models:
                m.status = "PROCESSING"
                m.locked_by = worker_id
                m.lock_expires_at = lease_expires
                m.attempts += 1
                m.version += 1
                claimed.append(self._to_entity(m))

            # Two-phase worker claiming: COMMIT lease immediately so other workers cannot claim
            await sess.commit()
            return claimed

    async def mark_published(self, id: str, processed_at: Optional[str] = None, session: Optional[Any] = None) -> None:
        async def _apply(s: Any) -> None:
            stmt = select(OutboxEventModel).where(OutboxEventModel.id == uuid.UUID(id))
            res = await s.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.status = "PUBLISHED"
                m.processed_at = datetime.fromisoformat(processed_at) if processed_at else datetime.now(timezone.utc)
                m.locked_by = None
                m.lock_expires_at = None
                m.last_error = None
                m.version += 1

        if session is not None:
            await _apply(session)
            return

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                await _apply(sess)
                await sess.commit()

    async def mark_failed(
        self,
        id: str,
        error: str,
        next_available_at: Optional[str] = None,
        max_attempts: int = 3,
        session: Optional[Any] = None,
    ) -> None:
        async def _apply(s: Any) -> None:
            stmt = select(OutboxEventModel).where(OutboxEventModel.id == uuid.UUID(id))
            res = await s.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.last_error = str(error)
                m.locked_by = None
                m.lock_expires_at = None
                m.version += 1
                if m.attempts >= max_attempts:
                    m.status = "FAILED"
                else:
                    m.status = "PENDING"
                    m.available_at = datetime.fromisoformat(next_available_at) if next_available_at else datetime.now(timezone.utc)

        if session is not None:
            await _apply(session)
            return

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                await _apply(sess)
                await sess.commit()

    async def retry(self, id: str, organization_id: str) -> OutboxEvent:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            raise RuntimeError("Database session unavailable.")

        async with db_manager._sessionmaker() as sess:
            stmt = select(OutboxEventModel).where(
                OutboxEventModel.id == uuid.UUID(id),
                OutboxEventModel.organization_id == uuid.UUID(organization_id),
            )
            res = await sess.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                raise EntityNotFoundException("Outbox event not found or does not belong to organization.")
            if m.status != "FAILED":
                raise BusinessRuleViolationException(f"Cannot retry event in status '{m.status}'. Only FAILED events can be retried.")

            m.status = "PENDING"
            m.available_at = datetime.now(timezone.utc)
            m.locked_by = None
            m.lock_expires_at = None
            m.version += 1
            await sess.commit()
            return self._to_entity(m)

    async def count_pending(self, organization_id: Optional[str] = None) -> int:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return 0

        async with db_manager._sessionmaker() as sess:
            stmt = select(func.count(OutboxEventModel.id)).where(
                OutboxEventModel.status.in_(["PENDING", "PROCESSING"])
            )
            if organization_id:
                stmt = stmt.where(OutboxEventModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            return int(res.scalar() or 0)

    async def count_failed(self, organization_id: Optional[str] = None) -> int:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return 0

        async with db_manager._sessionmaker() as sess:
            stmt = select(func.count(OutboxEventModel.id)).where(OutboxEventModel.status == "FAILED")
            if organization_id:
                stmt = stmt.where(OutboxEventModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            return int(res.scalar() or 0)

    async def get_oldest_pending_age_seconds(self, organization_id: Optional[str] = None) -> Optional[float]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return None

        async with db_manager._sessionmaker() as sess:
            stmt = select(func.min(OutboxEventModel.created_at)).where(
                OutboxEventModel.status.in_(["PENDING", "PROCESSING"])
            )
            if organization_id:
                stmt = stmt.where(OutboxEventModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            min_dt = res.scalar()
            if not min_dt:
                return None
            now = datetime.now(timezone.utc)
            return (now - min_dt).total_seconds()

    async def query_events(
        self,
        organization_id: str,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[OutboxEvent], int]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return [], 0

        async with db_manager._sessionmaker() as sess:
            base_stmt = select(OutboxEventModel).where(
                OutboxEventModel.organization_id == uuid.UUID(organization_id)
            )
            if event_type:
                base_stmt = base_stmt.where(OutboxEventModel.event_type.startswith(event_type))
            if aggregate_type:
                base_stmt = base_stmt.where(OutboxEventModel.aggregate_type == aggregate_type)
            if aggregate_id:
                base_stmt = base_stmt.where(OutboxEventModel.aggregate_id == str(aggregate_id))
            if status:
                base_stmt = base_stmt.where(OutboxEventModel.status == status)
            if start_time:
                base_stmt = base_stmt.where(OutboxEventModel.occurred_at >= datetime.fromisoformat(start_time))
            if end_time:
                base_stmt = base_stmt.where(OutboxEventModel.occurred_at <= datetime.fromisoformat(end_time))

            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            total_res = await sess.execute(count_stmt)
            total = int(total_res.scalar() or 0)

            query_stmt = base_stmt.order_by(OutboxEventModel.occurred_at.desc()).offset(offset).limit(limit)
            rows = (await sess.execute(query_stmt)).scalars().all()
            return [self._to_entity(r) for r in rows], total


class PostgresEventConsumptionRepository(IEventConsumptionRepository):
    """PostgreSQL-backed event consumption ledger with tenant scoping."""

    def __init__(self, session: Optional[Any] = None) -> None:
        self._session = session

    async def has_consumed(self, consumer_name: str, event_id: str, organization_id: Optional[str] = None) -> bool:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return False

        async with db_manager._sessionmaker() as sess:
            stmt = select(EventConsumptionModel).where(
                EventConsumptionModel.consumer_name == consumer_name,
                EventConsumptionModel.event_id == str(event_id),
            )
            if organization_id:
                stmt = stmt.where(EventConsumptionModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            return res.scalar_one_or_none() is not None

    async def record_consumption(self, consumption: EventConsumption, session: Optional[Any] = None) -> bool:
        async def _apply(s: Any) -> bool:
            stmt = select(EventConsumptionModel).where(
                EventConsumptionModel.consumer_name == consumption.consumer_name,
                EventConsumptionModel.event_id == str(consumption.event_id),
            )
            res = await s.execute(stmt)
            if res.scalar_one_or_none() is not None:
                return False

            consumed_dt = datetime.fromisoformat(consumption.consumed_at) if isinstance(consumption.consumed_at, str) else (consumption.consumed_at or datetime.now(timezone.utc))
            org_id = uuid.UUID(consumption.organization_id) if consumption.organization_id else None

            model = EventConsumptionModel(
                id=uuid.UUID(consumption.id) if isinstance(consumption.id, str) else consumption.id,
                consumer_name=consumption.consumer_name,
                event_id=str(consumption.event_id),
                organization_id=org_id,
                consumed_at=consumed_dt,
                status=consumption.status,
                error=consumption.error,
            )
            s.add(model)
            return True

        if session is not None:
            return await _apply(session)

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                recorded = await _apply(sess)
                if recorded:
                    await sess.commit()
                return recorded
        return False

    async def get_consumption(self, consumer_name: str, event_id: str, organization_id: Optional[str] = None) -> Optional[EventConsumption]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return None

        async with db_manager._sessionmaker() as sess:
            stmt = select(EventConsumptionModel).where(
                EventConsumptionModel.consumer_name == consumer_name,
                EventConsumptionModel.event_id == str(event_id),
            )
            if organization_id:
                stmt = stmt.where(EventConsumptionModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return None
            return EventConsumption(
                id=str(m.id),
                consumer_name=m.consumer_name,
                event_id=m.event_id,
                organization_id=str(m.organization_id) if m.organization_id else None,
                consumed_at=m.consumed_at.isoformat() if hasattr(m.consumed_at, "isoformat") else str(m.consumed_at),
                status=m.status,
                error=m.error,
            )


class PostgresWebhookRepository(IWebhookRepository):
    """PostgreSQL-backed webhook repository with secret encryption at rest."""

    def __init__(self, session: Optional[Any] = None) -> None:
        self._session = session

    def _to_entity(self, m: WebhookEndpointModel, decrypt: bool = False) -> WebhookEndpoint:
        secret_val = decrypt_secret(m.secret) if decrypt else m.secret
        return WebhookEndpoint(
            id=str(m.id),
            organization_id=str(m.organization_id),
            name=m.name,
            url=m.url,
            secret=secret_val,
            active=m.active,
            subscribed_event_types=m.subscribed_event_types if m.subscribed_event_types is not None else ["*"],
        )

    async def create(self, webhook: WebhookEndpoint, session: Optional[Any] = None) -> WebhookEndpoint:
        encrypted_sec = encrypt_secret(webhook.secret)
        model = WebhookEndpointModel(
            id=uuid.UUID(webhook.id) if isinstance(webhook.id, str) else webhook.id,
            organization_id=uuid.UUID(webhook.organization_id) if isinstance(webhook.organization_id, str) else webhook.organization_id,
            name=webhook.name,
            url=webhook.url,
            secret=encrypted_sec,
            active=webhook.active,
            subscribed_event_types=webhook.subscribed_event_types,
        )

        if session is not None:
            session.add(model)
            return webhook

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                sess.add(model)
                await sess.commit()
        return webhook

    async def get_by_id(self, id: str, organization_id: Optional[str] = None, decrypt_secret_val: bool = False) -> Optional[WebhookEndpoint]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return None

        async with db_manager._sessionmaker() as sess:
            stmt = select(WebhookEndpointModel).where(WebhookEndpointModel.id == uuid.UUID(id))
            if organization_id:
                stmt = stmt.where(WebhookEndpointModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            m = res.scalar_one_or_none()
            return self._to_entity(m, decrypt=decrypt_secret_val) if m else None

    async def list_by_org(self, organization_id: str) -> List[WebhookEndpoint]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return []

        async with db_manager._sessionmaker() as sess:
            stmt = select(WebhookEndpointModel).where(WebhookEndpointModel.organization_id == uuid.UUID(organization_id))
            res = await sess.execute(stmt)
            return [self._to_entity(m, decrypt=False) for m in res.scalars().all()]

    async def update(self, webhook: WebhookEndpoint, session: Optional[Any] = None) -> WebhookEndpoint:
        encrypted_sec = encrypt_secret(webhook.secret)
        async def _apply(s: Any) -> None:
            stmt = select(WebhookEndpointModel).where(WebhookEndpointModel.id == uuid.UUID(webhook.id))
            res = await s.execute(stmt)
            m = res.scalar_one_or_none()
            if m:
                m.name = webhook.name
                m.url = webhook.url
                m.secret = encrypted_sec
                m.active = webhook.active
                m.subscribed_event_types = webhook.subscribed_event_types

        if session is not None:
            await _apply(session)
            return webhook

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                await _apply(sess)
                await sess.commit()
        return webhook

    async def delete(self, id: str, organization_id: str, session: Optional[Any] = None) -> bool:
        async def _apply(s: Any) -> bool:
            stmt = select(WebhookEndpointModel).where(
                WebhookEndpointModel.id == uuid.UUID(id),
                WebhookEndpointModel.organization_id == uuid.UUID(organization_id),
            )
            res = await s.execute(stmt)
            m = res.scalar_one_or_none()
            if not m:
                return False
            await s.delete(m)
            return True

        if session is not None:
            return await _apply(session)

        if HAS_SQLALCHEMY and db_manager._sessionmaker:
            async with db_manager._sessionmaker() as sess:
                deleted = await _apply(sess)
                if deleted:
                    await sess.commit()
                return deleted
        return False

    async def find_subscribers(self, organization_id: str, event_type: str, decrypt_secret_val: bool = True) -> List[WebhookEndpoint]:
        if not HAS_SQLALCHEMY or not db_manager._sessionmaker:
            return []

        async with db_manager._sessionmaker() as sess:
            stmt = select(WebhookEndpointModel).where(
                WebhookEndpointModel.organization_id == uuid.UUID(organization_id),
                WebhookEndpointModel.active == True,
            )
            res = await sess.execute(stmt)
            models = res.scalars().all()
            matched: List[WebhookEndpoint] = []
            for m in models:
                ep = self._to_entity(m, decrypt=decrypt_secret_val)
                if ep.matches_event(event_type):
                    matched.append(ep)
            return matched


# ==============================================================================
# 3. Dynamic Dependency Injection Singletons
# ==============================================================================

# Default runtime wiring adapts dynamically based on whether SQLAlchemy engine is available
if HAS_SQLALCHEMY and getattr(db_manager, "_sessionmaker", None) is not None:
    outbox_repository: IOutboxRepository = PostgresOutboxRepository()
    consumption_repository: IEventConsumptionRepository = PostgresEventConsumptionRepository()
    webhook_repository: IWebhookRepository = PostgresWebhookRepository()
else:
    outbox_repository: IOutboxRepository = InMemoryOutboxRepository()
    consumption_repository: IEventConsumptionRepository = InMemoryEventConsumptionRepository()
    webhook_repository: IWebhookRepository = InMemoryWebhookRepository()


# ==============================================================================
# 4. Production DI Factories and Providers
# ==============================================================================

def get_outbox_repository(session: Optional[Any] = None) -> IOutboxRepository:
    """Production dependency injection factory for Outbox repository.
    
    Enforces that production runtime uses PostgresOutboxRepository.
    In testing/offline environments without database configured, falls back to the shared singleton.
    """
    from industrial_oracle.core.config import settings
    if settings.ENVIRONMENT == "production" or (HAS_SQLALCHEMY and getattr(db_manager, "_sessionmaker", None) is not None):
        return PostgresOutboxRepository(session=session)
    return outbox_repository


def get_consumption_repository(session: Optional[Any] = None) -> IEventConsumptionRepository:
    """Production dependency injection factory for Event Consumption repository."""
    from industrial_oracle.core.config import settings
    if settings.ENVIRONMENT == "production" or (HAS_SQLALCHEMY and getattr(db_manager, "_sessionmaker", None) is not None):
        return PostgresEventConsumptionRepository(session=session)
    return consumption_repository


def get_webhook_repository(session: Optional[Any] = None) -> IWebhookRepository:
    """Production dependency injection factory for Webhook repository."""
    from industrial_oracle.core.config import settings
    if settings.ENVIRONMENT == "production" or (HAS_SQLALCHEMY and getattr(db_manager, "_sessionmaker", None) is not None):
        return PostgresWebhookRepository(session=session)
    return webhook_repository
