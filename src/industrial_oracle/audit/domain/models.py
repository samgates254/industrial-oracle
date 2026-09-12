"""Audit domain models."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from industrial_oracle.shared.domain.entity import Entity


class AuditLog(Entity):
    """Immutable audit record for compliance and security traceability."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: Optional[uuid.UUID] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        timestamp: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.actor_id = actor_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.old_value = old_value
        self.new_value = new_value
        self.reason = reason
        self.request_id = request_id
        self.timestamp = timestamp or created_at or datetime.now(timezone.utc)
