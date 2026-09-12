"""FastAPI router for Operations: Work Orders and Production Runs."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status

from industrial_oracle.core.security import PermissionEnum, TenantContext, get_tenant_context
from industrial_oracle.operations.application.dtos import (
    MaterialConsumeDTO,
    MaterialConsumptionResponseDTO,
    ProductionQuantityRecordDTO,
    ProductionRunActionDTO,
    ProductionRunCreateDTO,
    ProductionRunResponseDTO,
    WorkOrderActionDTO,
    WorkOrderCreateDTO,
    WorkOrderResponseDTO,
    WorkOrderUpdateDTO,
)
from industrial_oracle.operations.application.services import production_run_service, work_order_service

router = APIRouter(prefix="/api/v1", tags=["Operations"])


# ==============================================================================
# 1. Work Orders
# ==============================================================================

@router.post("/work-orders", response_model=WorkOrderResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    dto: WorkOrderCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_CREATE)
    return await work_order_service.create_work_order(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.get("/work-orders", response_model=List[WorkOrderResponseDTO])
async def list_work_orders(
    plant_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    work_order_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[WorkOrderResponseDTO]:
    tenant.require_permission(PermissionEnum.OPERATIONS_READ)
    return await work_order_service.list_work_orders(
        tenant.organization_id,
        plant_id=plant_id,
        status=status,
        work_order_type=work_order_type,
        limit=limit,
        offset=offset,
    )


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponseDTO)
async def get_work_order(
    work_order_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_READ)
    return await work_order_service.get_work_order(tenant.organization_id, work_order_id)


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrderResponseDTO)
async def update_work_order(
    work_order_id: uuid.UUID,
    dto: WorkOrderUpdateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await work_order_service.update_work_order(tenant.organization_id, work_order_id, dto, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/release", response_model=WorkOrderResponseDTO)
async def release_work_order(
    work_order_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await work_order_service.release_work_order(tenant.organization_id, work_order_id, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/start", response_model=WorkOrderResponseDTO)
async def start_work_order(
    work_order_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await work_order_service.start_work_order(tenant.organization_id, work_order_id, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/hold", response_model=WorkOrderResponseDTO)
async def hold_work_order(
    work_order_id: uuid.UUID,
    action: Optional[WorkOrderActionDTO] = None,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    reason = action.reason if action else None
    return await work_order_service.hold_work_order(tenant.organization_id, work_order_id, reason, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/resume", response_model=WorkOrderResponseDTO)
async def resume_work_order(
    work_order_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await work_order_service.resume_work_order(tenant.organization_id, work_order_id, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/complete", response_model=WorkOrderResponseDTO)
async def complete_work_order(
    work_order_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await work_order_service.complete_work_order(tenant.organization_id, work_order_id, actor_id=tenant.user_id)


@router.post("/work-orders/{work_order_id}/cancel", response_model=WorkOrderResponseDTO)
async def cancel_work_order(
    work_order_id: uuid.UUID,
    action: Optional[WorkOrderActionDTO] = None,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WorkOrderResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    reason = action.reason if action else None
    return await work_order_service.cancel_work_order(tenant.organization_id, work_order_id, reason, actor_id=tenant.user_id)


# ==============================================================================
# 2. Production Runs
# ==============================================================================

@router.post("/production-runs", response_model=ProductionRunResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_production_run(
    dto: ProductionRunCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_CREATE)
    return await production_run_service.create_production_run(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.get("/production-runs", response_model=List[ProductionRunResponseDTO])
async def list_production_runs(
    production_line_id: Optional[uuid.UUID] = Query(None),
    work_order_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[ProductionRunResponseDTO]:
    tenant.require_permission(PermissionEnum.OPERATIONS_READ)
    return await production_run_service.list_production_runs(
        tenant.organization_id,
        production_line_id=production_line_id,
        work_order_id=work_order_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/production-runs/{run_id}", response_model=ProductionRunResponseDTO)
async def get_production_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_READ)
    return await production_run_service.get_production_run(tenant.organization_id, run_id)


@router.post("/production-runs/{run_id}/start", response_model=ProductionRunResponseDTO)
async def start_production_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.start_production_run(tenant.organization_id, run_id, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/pause", response_model=ProductionRunResponseDTO)
async def pause_production_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.pause_production_run(tenant.organization_id, run_id, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/resume", response_model=ProductionRunResponseDTO)
async def resume_production_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.resume_production_run(tenant.organization_id, run_id, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/quantity", response_model=ProductionRunResponseDTO)
async def record_production_quantity(
    run_id: uuid.UUID,
    dto: ProductionQuantityRecordDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.record_quantity(tenant.organization_id, run_id, dto, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/complete", response_model=ProductionRunResponseDTO)
async def complete_production_run(
    run_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.complete_production_run(tenant.organization_id, run_id, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/abort", response_model=ProductionRunResponseDTO)
async def abort_production_run(
    run_id: uuid.UUID,
    action: ProductionRunActionDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ProductionRunResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    reason = action.reason or "Aborted by operator"
    return await production_run_service.abort_production_run(tenant.organization_id, run_id, reason, actor_id=tenant.user_id)


@router.post("/production-runs/{run_id}/materials/consume", response_model=MaterialConsumptionResponseDTO, status_code=status.HTTP_201_CREATED)
async def consume_production_run_material(
    run_id: uuid.UUID,
    dto: MaterialConsumeDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MaterialConsumptionResponseDTO:
    tenant.require_permission(PermissionEnum.OPERATIONS_UPDATE)
    return await production_run_service.consume_material(tenant.organization_id, run_id, dto, actor_id=tenant.user_id)
