"""Audit log repository implementations."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.audit.domain.models import AuditLog
from industrial_oracle.shared.application.repository import GenericRepository


class IAuditLogRepository(GenericRepository[AuditLog, uuid.UUID]):
    pass


class InMemoryAuditLogRepository(IAuditLogRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, AuditLog] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[AuditLog]:
        return self._storage.get(entity_id)

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[AuditLog]:
        logs = [l for l in self._storage.values() if l.organization_id == organization_id]
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[offset : offset + limit]

    async def add(self, entity: AuditLog) -> AuditLog:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: AuditLog) -> AuditLog:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


audit_repo = InMemoryAuditLogRepository()
