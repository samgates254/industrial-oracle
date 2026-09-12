"""Audit service for logging security and state mutations."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional
import uuid

from industrial_oracle.audit.domain.models import AuditLog
from industrial_oracle.audit.infrastructure.repository import audit_repo
from industrial_oracle.core.logging import request_id_ctx
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.infrastructure.event_bus import event_bus


class AuditService:
    """Records audit logs and emits audit events."""

    def __init__(self, repository=audit_repo) -> None:
        self.repo = repository

    async def record_action(
        self,
        organization_id: uuid.UUID,
        actor_id: Optional[uuid.UUID],
        action: str,
        resource_type: str,
        resource_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> AuditLog:
        req_id = request_id_ctx.get()
        log_entry = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            reason=reason,
            request_id=req_id,
            timestamp=datetime.now(timezone.utc),
        )
        await self.repo.add(log_entry)

        # Emit audit domain event
        await event_bus.publish(
            DomainEvent(
                event_type="AuditEventRecorded",
                aggregate_id=str(log_entry.id),
                aggregate_type="AuditLog",
                organization_id=str(organization_id),
                payload={
                    "action": action,
                    "actor_id": str(actor_id) if actor_id else None,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                },
            )
        )
        return log_entry



    async def log_action(
        self,
        organization_id: Any,
        actor_id: Optional[Any],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Any = None,
        target_entity: Optional[str] = None,
        target_id: Any = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> AuditLog:
        """Convenience alias supporting flexible caller keyword arguments."""
        actual_res_type = resource_type or target_entity or "Unknown"
        actual_res_id = str(resource_id if resource_id is not None else (target_id if target_id is not None else ""))
        actual_org_id = uuid.UUID(str(organization_id)) if organization_id else uuid.uuid4()
        actual_actor_id = uuid.UUID(str(actor_id)) if actor_id else None
        return await self.record_action(
            organization_id=actual_org_id,
            actor_id=actual_actor_id,
            action=action,
            resource_type=actual_res_type,
            resource_id=actual_res_id,
            old_value=old_value or metadata or details,
            new_value=new_value,
            reason=reason,
        )


audit_service = AuditService()
