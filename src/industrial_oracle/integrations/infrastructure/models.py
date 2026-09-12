"""SQLAlchemy declarative models for outbox, consumptions, and webhooks."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from industrial_oracle.core.database import (
    HAS_SQLALCHEMY,
    ModelBase,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Column,
)

if HAS_SQLALCHEMY:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
    from sqlalchemy.orm import Mapped, mapped_column

    class OutboxEventModel(ModelBase):
        __tablename__ = "outbox_events"

        organization_id: Mapped[uuid.UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        event_id: Mapped[uuid.UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            unique=True,
            nullable=False,
            index=True,
        )
        event_type: Mapped[str] = mapped_column(String(100), nullable=False)
        aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
        aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
        payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
        occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
        attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
        available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
        processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
        last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
        causation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
        locked_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        lock_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

        __table_args__ = (
            Index("ix_outbox_events_status_available", "status", "available_at"),
            Index("ix_outbox_events_org_status", "organization_id", "status"),
            Index("ix_outbox_events_aggregate", "aggregate_type", "aggregate_id"),
        )

    class EventConsumptionModel(ModelBase):
        __tablename__ = "event_consumptions"

        organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        )
        consumer_name: Mapped[str] = mapped_column(String(100), nullable=False)
        event_id: Mapped[str] = mapped_column(String(100), nullable=False)
        consumed_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
        status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
        error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

        __table_args__ = (
            Index("ix_event_consumptions_unique", "consumer_name", "event_id", unique=True),
            Index("ix_event_consumptions_org_consumer", "organization_id", "consumer_name"),
        )

    class WebhookEndpointModel(ModelBase):
        __tablename__ = "webhook_endpoints"

        organization_id: Mapped[uuid.UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        url: Mapped[str] = mapped_column(String(500), nullable=False)
        secret: Mapped[str] = mapped_column(String(255), nullable=False)
        active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
        subscribed_event_types: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=lambda: ["*"])

else:
    # Stub models for non-SQLAlchemy testing environments
    class OutboxEventModel(ModelBase):
        __tablename__ = "outbox_events"

    class EventConsumptionModel(ModelBase):
        __tablename__ = "event_consumptions"

    class WebhookEndpointModel(ModelBase):
        __tablename__ = "webhook_endpoints"
