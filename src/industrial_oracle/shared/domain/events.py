"""Domain events specification and base event envelope."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class DomainEvent(BaseModel):
    """Base domain event envelope.

    Attributes:
        event_id: Unique event identifier (UUID v4)
        event_type: Qualified name of the domain event
        aggregate_id: Identifier of the aggregate root
        aggregate_type: Type name of the aggregate
        occurred_at: UTC timestamp when the event occurred
        organization_id: Organization context identifier
        payload: Event payload dictionary
        event_version: Semantic version of the event schema (default "v1")
        correlation_id: Distributed trace or end-to-end operation identifier
        causation_id: Identifier of the event that directly triggered this event
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    organization_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    event_version: str = "v1"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
