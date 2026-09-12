"""FastAPI router for Maintenance bounded context."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status

from industrial_oracle.core.security import PermissionEnum, TenantContext, get_tenant_context
from industrial_oracle.maintenance.application.dtos import (
    MaintenanceCompleteDTO,
    MaintenanceOrderCreateDTO,
    MaintenanceOrderResponseDTO,
)
from industrial_oracle.maintenance.application.services import maintenance_service
from industrial_oracle.operations.application.dtos import MaterialConsumeDTO, MaterialConsumptionResponseDTO

router = APIRouter(prefix="/api/v1/maintenance", tags=["Maintenance"])


@router.post("/work-orders", response_model=MaintenanceOrderResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_maintenance_order(
    dto: MaintenanceOrderCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaintenanceOrderResponseDTO:
    tenant.require_permission(PermissionEnum.MAINTENANCE_CREATE)
    return await maintenance_service.create_maintenance_order(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.get("/work-orders", response_model=List[MaintenanceOrderResponseDTO])
async def list_maintenance_orders(
    asset_id: Optional[uuid.UUID] = Query(None),
    machine_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[MaintenanceOrderResponseDTO]:
    tenant.require_permission(PermissionEnum.MAINTENANCE_READ)
    return await maintenance_service.list_maintenance_orders(
        tenant.organization_id, asset_id=asset_id, machine_id=machine_id, status=status, limit=limit, offset=offset
    )


@router.get("/work-orders/{maintenance_id}", response_model=MaintenanceOrderResponseDTO)
async def get_maintenance_order(
    maintenance_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaintenanceOrderResponseDTO:
    tenant.require_permission(PermissionEnum.MAINTENANCE_READ)
    return await maintenance_service.get_maintenance_order(tenant.organization_id, maintenance_id)


@router.post("/work-orders/{maintenance_id}/start", response_model=MaintenanceOrderResponseDTO)
async def start_maintenance_order(
    maintenance_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaintenanceOrderResponseDTO:
    tenant.require_permission(PermissionEnum.MAINTENANCE_UPDATE)
    return await maintenance_service.start_maintenance(tenant.organization_id, maintenance_id, actor_id=tenant.user_id)


@router.post("/work-orders/{maintenance_id}/complete", response_model=MaintenanceOrderResponseDTO)
async def complete_maintenance_order(
    maintenance_id: uuid.UUID,
    dto: Optional[MaintenanceCompleteDTO] = None,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaintenanceOrderResponseDTO:
    tenant.require_permission(PermissionEnum.MAINTENANCE_UPDATE)
    complete_dto = dto or MaintenanceCompleteDTO()
    return await maintenance_service.complete_maintenance(
        tenant.organization_id, maintenance_id, complete_dto, actor_id=tenant.user_id
    )


@router.post(
    "/work-orders/{maintenance_id}/materials/consume",
    response_model=MaterialConsumptionResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def consume_maintenance_material(
    maintenance_id: uuid.UUID,
    dto: MaterialConsumeDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaterialConsumptionResponseDTO:
    tenant.require_permission(PermissionEnum.MAINTENANCE_UPDATE)
    return await maintenance_service.consume_material(tenant.organization_id, maintenance_id, dto, actor_id=tenant.user_id)
