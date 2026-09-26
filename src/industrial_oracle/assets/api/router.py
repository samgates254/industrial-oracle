"""Assets, Production Lines, Machines, and Telemetry API router."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status

from industrial_oracle.assets.application.dtos import (
    AssetCreateDTO,
    AssetResponseDTO,
    AssetStatusUpdateDTO,
    AssetUpdateDTO,
    MachineCreateDTO,
    MachineFaultDTO,
    MachineHoursDTO,
    MachineResponseDTO,
    MachineUpdateDTO,
    ProductionLineCreateDTO,
    ProductionLineResponseDTO,
    TelemetryPointCreateDTO,
    TelemetryPointResponseDTO,
)
from industrial_oracle.assets.application.services import (
    AssetService,
    MachineService,
    ProductionLineService,
    TelemetryService,
)
from industrial_oracle.assets.infrastructure.repository import (
    asset_repo,
    machine_repo,
    production_line_repo,
    telemetry_point_repo,
)
from industrial_oracle.core.security import (
    PermissionEnum,
    TenantContext,
    get_tenant_context,
    require_permission,
)
from industrial_oracle.organization.infrastructure.repository import plant_repo

router = APIRouter(prefix="/api/v1", tags=["Assets, Lines & Machinery"])

asset_service = AssetService(asset_repo, plant_repo)
line_service = ProductionLineService(production_line_repo, plant_repo)
machine_service = MachineService(machine_repo, asset_repo, production_line_repo)
telemetry_service = TelemetryService(telemetry_point_repo, machine_repo)


# ==============================================================================
# Asset Endpoints
# ==============================================================================

@router.post(
    "/assets",
    response_model=AssetResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_CREATE))],
)
async def create_asset(
    dto: AssetCreateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Creates an industrial asset within the caller's organization."""
    return await asset_service.create_asset(dto, ctx.organization.id, ctx.user.id)


@router.get(
    "/assets",
    response_model=List[AssetResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def list_assets(
    plant_id: Optional[uuid.UUID] = Query(None, description="Optional plant filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists assets belonging strictly to the caller's organization."""
    return await asset_service.list_assets(
        organization_id=ctx.organization.id,
        plant_id=plant_id,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/assets/{asset_id}",
    response_model=AssetResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def get_asset(
    asset_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Retrieves a specific asset if owned by caller's organization."""
    return await asset_service.get_asset(asset_id, ctx.organization.id)


@router.patch(
    "/assets/{asset_id}",
    response_model=AssetResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_UPDATE))],
)
async def update_asset(
    asset_id: uuid.UUID,
    dto: AssetUpdateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Updates asset attributes."""
    return await asset_service.update_asset(asset_id, dto, ctx.organization.id, ctx.user.id)


@router.patch(
    "/assets/{asset_id}/status",
    response_model=AssetResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_UPDATE))],
)
async def update_asset_status(
    asset_id: uuid.UUID,
    dto: AssetStatusUpdateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Transitions asset operational state (IN_SERVICE, MAINTENANCE, OUT_OF_SERVICE, DECOMMISSIONED)."""
    return await asset_service.change_asset_status(asset_id, dto.status, ctx.organization.id, ctx.user.id)


@router.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_DELETE))],
)
async def delete_asset(
    asset_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Deletes an asset from the catalog."""
    await asset_service.delete_asset(asset_id, ctx.organization.id, ctx.user.id)


# ==============================================================================
# Production Line Endpoints
# ==============================================================================

@router.post(
    "/production-lines",
    response_model=ProductionLineResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_CREATE))],
)
async def create_production_line(
    dto: ProductionLineCreateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Creates a production line within a plant owned by caller's organization."""
    return await line_service.create_production_line(dto, ctx.organization.id, ctx.user.id)


@router.get(
    "/production-lines",
    response_model=List[ProductionLineResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def list_production_lines(
    plant_id: Optional[uuid.UUID] = Query(None, description="Optional plant filter"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists production lines for the caller's organization."""
    return await line_service.list_production_lines(
        organization_id=ctx.organization.id,
        plant_id=plant_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/production-lines/{line_id}",
    response_model=ProductionLineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def get_production_line(
    line_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Retrieves details of a specific production line."""
    return await line_service.get_production_line(line_id, ctx.organization.id)


# ==============================================================================
# Machine Endpoints
# ==============================================================================

@router.post(
    "/machines",
    response_model=MachineResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_CREATE))],
)
async def create_machine(
    dto: MachineCreateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Registers an operating machine bound to a physical asset."""
    return await machine_service.create_machine(dto, ctx.organization.id, ctx.user.id)


@router.get(
    "/machines",
    response_model=List[MachineResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def list_machines(
    production_line_id: Optional[uuid.UUID] = Query(None, description="Optional line filter"),
    status: Optional[str] = Query(None, description="Optional status filter"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists machines belonging strictly to caller's organization."""
    return await machine_service.list_machines(
        organization_id=ctx.organization.id,
        production_line_id=production_line_id,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/machines/{machine_id}",
    response_model=MachineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def get_machine(
    machine_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Retrieves machine status and operational telemetry summary."""
    return await machine_service.get_machine(machine_id, ctx.organization.id)


@router.post(
    "/machines/{machine_id}/start",
    response_model=MachineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.OPERATIONS_UPDATE))],
)
async def start_machine(
    machine_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Transitions machine operational state to RUNNING."""
    return await machine_service.start_machine(machine_id, ctx.organization.id, ctx.user.id)


@router.post(
    "/machines/{machine_id}/stop",
    response_model=MachineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.OPERATIONS_UPDATE))],
)
async def stop_machine(
    machine_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Transitions machine operational state to STOPPED."""
    return await machine_service.stop_machine(machine_id, ctx.organization.id, ctx.user.id)


@router.post(
    "/machines/{machine_id}/fault",
    response_model=MachineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.OPERATIONS_UPDATE))],
)
async def record_machine_fault(
    machine_id: uuid.UUID,
    dto: MachineFaultDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Records an equipment fault, transitioning machine state to FAULTED."""
    return await machine_service.record_machine_fault(machine_id, dto, ctx.organization.id, ctx.user.id)


@router.post(
    "/machines/{machine_id}/clear-fault",
    response_model=MachineResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.OPERATIONS_UPDATE))],
)
async def clear_machine_fault(
    machine_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Clears machine fault condition, restoring machine state to STOPPED."""
    return await machine_service.clear_machine_fault(machine_id, ctx.organization.id, ctx.user.id)


@router.post(
    "/machines/{machine_id}/telemetry-points",
    response_model=TelemetryPointResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_UPDATE))],
)
async def bind_telemetry_point(
    machine_id: uuid.UUID,
    dto: TelemetryPointCreateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Binds a telemetry channel (vibration, temperature, etc.) to an operational machine."""
    return await telemetry_service.bind_telemetry_point(machine_id, dto, ctx.organization.id, ctx.user.id)


@router.get(
    "/machines/{machine_id}/telemetry-points",
    response_model=List[TelemetryPointResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ASSETS_READ))],
)
async def list_machine_telemetry_points(
    machine_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Lists telemetry channels registered on a machine."""
    return await telemetry_service.list_machine_telemetry(machine_id, ctx.organization.id)
