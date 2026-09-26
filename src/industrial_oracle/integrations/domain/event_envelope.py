"""Canonical event envelope for reliable integration and external messaging.

Independent of FastAPI and HTTP transport layers.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional
import uuid


class EventEnvelope:
    """Canonical event envelope ensuring stable integration contracts across systems.

    Attributes:
        event_id: Globally unique identifier for this event instance.
        event_type: Qualified semantic event name (e.g., 'WorkOrderCompleted').
        event_version: Schema version string (e.g., 'v1').
        occurred_at: ISO 8601 UTC timestamp of original domain occurrence.
        organization_id: Multi-tenant boundary identifier.
        aggregate_type: Domain aggregate name (e.g., 'WorkOrder', 'ProductionRun').
        aggregate_id: Primary key of the originating aggregate root.
        payload: Clean JSON-serializable dictionary with domain event data.
        correlation_id: Distributed operation trace ID (originating request/action).
        causation_id: Event ID that directly caused this event.
    """

    def __init__(
        self,
        event_id: Optional[str] = None,
        event_type: str = "",
        event_version: str = "v1",
        occurred_at: Optional[str] = None,
        organization_id: str = "",
        aggregate_type: str = "",
        aggregate_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> None:
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.event_version = event_version or "v1"
        self.occurred_at = occurred_at or datetime.now(timezone.utc).isoformat()
        self.organization_id = str(organization_id)
        self.aggregate_type = aggregate_type
        self.aggregate_id = str(aggregate_id)
        self.payload = payload if payload is not None else {}
        self.correlation_id = correlation_id
        self.causation_id = causation_id

    @property
    def qualified_event_type(self) -> str:
        """Returns the versioned event type, e.g. 'WorkOrderCompleted.v1'."""
        if self.event_type.endswith(f".{self.event_version}"):
            return self.event_type
        return f"{self.event_type}.{self.event_version}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the envelope to a standard python dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "qualified_event_type": self.qualified_event_type,
            "occurred_at": self.occurred_at,
            "organization_id": self.organization_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "payload": self.payload,
        }

    def to_json(self) -> str:
        """Serializes the envelope to a JSON formatted string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        """Deserializes a dictionary into an EventEnvelope instance."""
        raw_type = data.get("event_type", "")
        raw_version = data.get("event_version", "v1")

        # Parse type if qualified format like 'WorkOrderCreated.v1' is provided
        if "." in raw_type and not data.get("event_version"):
            parts = raw_type.rsplit(".", 1)
            event_type = parts[0]
            event_version = parts[1]
        else:
            event_type = raw_type
            event_version = raw_version

        return cls(
            event_id=data.get("event_id"),
            event_type=event_type,
            event_version=event_version,
            occurred_at=data.get("occurred_at"),
            organization_id=str(data.get("organization_id", "")),
            aggregate_type=data.get("aggregate_type", ""),
            aggregate_id=str(data.get("aggregate_id", "")),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EventEnvelope":
        """Deserializes a JSON string into an EventEnvelope instance."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_domain_event(
        cls,
        domain_event: Any,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_version: str = "v1",
    ) -> "EventEnvelope":
        """Converts an internal DomainEvent into a Canonical EventEnvelope."""
        raw_type = getattr(domain_event, "event_type", "UnknownEvent")
        if "." in raw_type:
            parts = raw_type.rsplit(".", 1)
            ev_type = parts[0]
            version = parts[1]
        else:
            ev_type = raw_type
            version = getattr(domain_event, "event_version", event_version) or event_version

        return cls(
            event_id=getattr(domain_event, "event_id", None) or str(uuid.uuid4()),
            event_type=ev_type,
            event_version=version,
            occurred_at=getattr(domain_event, "occurred_at", None),
            organization_id=str(getattr(domain_event, "organization_id", "")),
            aggregate_type=getattr(domain_event, "aggregate_type", ""),
            aggregate_id=str(getattr(domain_event, "aggregate_id", "")),
            payload=getattr(domain_event, "payload", {}) or {},
            correlation_id=correlation_id or getattr(domain_event, "correlation_id", None),
            causation_id=causation_id or getattr(domain_event, "causation_id", None),
        )
