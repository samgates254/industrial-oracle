"""Base Domain Entity and Aggregate Root abstractions."""

from abc import ABC
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from industrial_oracle.shared.domain.events import DomainEvent


class Entity(ABC):
    """Base class for all domain entities."""

    def __init__(
        self,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class AggregateRoot(Entity):
    """Base class for domain aggregate roots that record domain events."""

    def __init__(
        self,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self._domain_events: List[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        """Records a domain event for post-commit dispatch."""
        self._domain_events.append(event)

    def get_events(self) -> List[DomainEvent]:
        """Returns recorded domain events without clearing them."""
        return list(self._domain_events)

    def clear_events(self) -> None:
        """Explicitly clears recorded domain events after successful persistence."""
        self._domain_events.clear()

    def collect_events(self) -> List[DomainEvent]:
        """Returns and clears all recorded domain events (legacy compatibility)."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
