"""Outbox domain entity and state transitions."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException


class OutboxStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class OutboxEvent:
    """Represents a durable outbox record stored within a business transaction."""

    def __init__(
        self,
        id: Optional[str] = None,
        organization_id: str = "",
        event_id: Optional[str] = None,
        event_type: str = "",
        aggregate_type: str = "",
        aggregate_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        occurred_at: Optional[str] = None,
        created_at: Optional[str] = None,
        status: OutboxStatus = OutboxStatus.PENDING,
        attempts: int = 0,
        available_at: Optional[str] = None,
        processed_at: Optional[str] = None,
        last_error: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        version: int = 1,
        locked_by: Optional[str] = None,
        lock_expires_at: Optional[str] = None,
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        self.id = id or str(uuid.uuid4())
        self.organization_id = str(organization_id)
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_type = aggregate_type
        self.aggregate_id = str(aggregate_id)
        self.payload = payload if payload is not None else {}
        self.occurred_at = occurred_at or now_str
        self.created_at = created_at or now_str
        self.status = status if isinstance(status, OutboxStatus) else OutboxStatus(status)
        self.attempts = attempts
        self.available_at = available_at or now_str
        self.processed_at = processed_at
        self.last_error = last_error
        self.correlation_id = correlation_id
        self.causation_id = causation_id
        self.version = version
        self.locked_by = locked_by
        self.lock_expires_at = lock_expires_at

    def mark_processing(self, worker_id: str, lease_seconds: int = 30) -> None:
        """Claims the outbox event for processing by a specific worker."""
        if self.status == OutboxStatus.PUBLISHED:
            raise BusinessRuleViolationException("Cannot claim an already published event.")
        
        now = datetime.now(timezone.utc)
        self.status = OutboxStatus.PROCESSING
        self.locked_by = worker_id
        self.lock_expires_at = (now + timedelta(seconds=lease_seconds)).isoformat()
        self.attempts += 1
        self.version += 1

    def mark_published(self, processed_at: Optional[str] = None) -> None:
        """Marks the event as successfully published/dispatched."""
        if self.status == OutboxStatus.PUBLISHED:
            return  # Idempotent
        self.status = OutboxStatus.PUBLISHED
        self.processed_at = processed_at or datetime.now(timezone.utc).isoformat()
        self.locked_by = None
        self.lock_expires_at = None
        self.last_error = None
        self.version += 1

    def mark_failed(
        self,
        error: str,
        next_available_at: Optional[str] = None,
        max_attempts: int = 3,
    ) -> None:
        """Records a publishing failure, scheduling retry or marking as FAILED."""
        self.last_error = str(error)
        self.locked_by = None
        self.lock_expires_at = None
        self.version += 1

        if self.attempts >= max_attempts:
            self.status = OutboxStatus.FAILED
        else:
            self.status = OutboxStatus.PENDING
            self.available_at = next_available_at or datetime.now(timezone.utc).isoformat()

    def retry(self) -> None:
        """Admin or system trigger to retry a failed event."""
        if self.status != OutboxStatus.FAILED:
            raise BusinessRuleViolationException(
                f"Cannot retry event in status '{self.status.value}'. Only FAILED events can be retried."
            )
        self.status = OutboxStatus.PENDING
        self.available_at = datetime.now(timezone.utc).isoformat()
        self.locked_by = None
        self.lock_expires_at = None
        self.version += 1

    def is_lock_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Checks whether an existing processing lock has expired."""
        if not self.lock_expires_at or self.status != OutboxStatus.PROCESSING:
            return True
        now = current_time or datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(self.lock_expires_at)
        return now >= expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
            "occurred_at": self.occurred_at,
            "created_at": self.created_at,
            "status": self.status.value,
            "attempts": self.attempts,
            "available_at": self.available_at,
            "processed_at": self.processed_at,
            "last_error": self.last_error,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
            "locked_by": self.locked_by,
            "lock_expires_at": self.lock_expires_at,
        }

    @classmethod
    def from_domain_event(
        cls,
        domain_event: Any,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_version: str = "v1",
    ) -> "OutboxEvent":
        raw_type = getattr(domain_event, "event_type", "UnknownEvent")
        if "." in raw_type:
            event_type = raw_type
        else:
            event_type = f"{raw_type}.{event_version}"

        payload = getattr(domain_event, "payload", {})
        if not isinstance(payload, dict):
            payload = {"data": payload}

        occurred_at = getattr(domain_event, "occurred_at", None)
        if occurred_at and hasattr(occurred_at, "isoformat"):
            occurred_at = occurred_at.isoformat()

        return cls(
            organization_id=str(getattr(domain_event, "organization_id", "")),
            event_type=event_type,
            aggregate_type=getattr(domain_event, "aggregate_type", "Aggregate"),
            aggregate_id=str(getattr(domain_event, "aggregate_id", "")),
            payload=payload,
            occurred_at=occurred_at,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
