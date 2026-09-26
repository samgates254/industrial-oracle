"""Event consumption and consumer idempotency record."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


class EventConsumption:
    """Represents a record of an event being consumed by an internal or adapter consumer.

    Enforces idempotent processing: consumer_name + event_id must be unique, scoped by organization.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        consumer_name: str = "",
        event_id: str = "",
        organization_id: Optional[str] = None,
        consumed_at: Optional[str] = None,
        status: str = "SUCCESS",
        error: Optional[str] = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.consumer_name = consumer_name
        self.event_id = str(event_id)
        self.organization_id = str(organization_id) if organization_id else None
        self.consumed_at = consumed_at or datetime.now(timezone.utc).isoformat()
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "consumer_name": self.consumer_name,
            "event_id": self.event_id,
            "organization_id": self.organization_id,
            "consumed_at": self.consumed_at,
            "status": self.status,
            "error": self.error,
        }
