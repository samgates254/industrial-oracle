"""FastAPI router for Inventory bounded context: Items, Locations, Receipts, Issues, Adjustments, Transfers, and Balances."""

from typing import List, Optional, Tuple
import uuid
from fastapi import APIRouter, Depends, Query, status

from industrial_oracle.core.security import PermissionEnum, TenantContext, get_tenant_context
from industrial_oracle.inventory.application.dtos import (
    InventoryAdjustmentDTO,
    InventoryBalanceResponseDTO,
    InventoryIssueDTO,
    InventoryLocationCreateDTO,
    InventoryLocationResponseDTO,
    InventoryReceiptDTO,
    InventoryTransferDTO,
    ItemCreateDTO,
    ItemResponseDTO,
    ItemUpdateDTO,
)
from industrial_oracle.inventory.application.services import inventory_service

router = APIRouter(prefix="/api/v1", tags=["Inventory"])


# ==============================================================================
# 1. Items
# ==============================================================================

@router.post("/items", response_model=ItemResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_item(
    dto: ItemCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ItemResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_CREATE)
    return await inventory_service.create_item(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.get("/items", response_model=List[ItemResponseDTO])
async def list_items(
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[ItemResponseDTO]:
    tenant.require_permission(PermissionEnum.INVENTORY_READ)
    return await inventory_service.list_items(tenant.organization_id, category=category, limit=limit, offset=offset)


@router.get("/items/{item_id}", response_model=ItemResponseDTO)
async def get_item(
    item_id: uuid.UUID,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ItemResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_READ)
    return await inventory_service.get_item(tenant.organization_id, item_id)


@router.patch("/items/{item_id}", response_model=ItemResponseDTO)
async def update_item(
    item_id: uuid.UUID,
    dto: ItemUpdateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ItemResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_UPDATE)
    return await inventory_service.update_item(tenant.organization_id, item_id, dto, actor_id=tenant.user_id)


# ==============================================================================
# 2. Locations
# ==============================================================================

@router.post("/inventory/locations", response_model=InventoryLocationResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_location(
    dto: InventoryLocationCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> InventoryLocationResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_CREATE)
    return await inventory_service.create_location(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.get("/inventory/locations", response_model=List[InventoryLocationResponseDTO])
async def list_locations(
    site_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[InventoryLocationResponseDTO]:
    tenant.require_permission(PermissionEnum.INVENTORY_READ)
    return await inventory_service.list_locations(tenant.organization_id, site_id=site_id, limit=limit, offset=offset)


# ==============================================================================
# 3. Stock Movements & Balances
# ==============================================================================

@router.post("/inventory/receipts", response_model=InventoryBalanceResponseDTO, status_code=status.HTTP_201_CREATED)
async def receive_stock(
    dto: InventoryReceiptDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> InventoryBalanceResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_UPDATE)
    return await inventory_service.receive_stock(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.post("/inventory/issues", response_model=InventoryBalanceResponseDTO)
async def issue_stock(
    dto: InventoryIssueDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> InventoryBalanceResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_UPDATE)
    return await inventory_service.issue_stock(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.post("/inventory/adjustments", response_model=InventoryBalanceResponseDTO)
async def adjust_stock(
    dto: InventoryAdjustmentDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> InventoryBalanceResponseDTO:
    tenant.require_permission(PermissionEnum.INVENTORY_UPDATE)
    return await inventory_service.adjust_stock(tenant.organization_id, dto, actor_id=tenant.user_id)


@router.post("/inventory/transfers", response_model=List[InventoryBalanceResponseDTO])
async def transfer_stock(
    dto: InventoryTransferDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[InventoryBalanceResponseDTO]:
    tenant.require_permission(PermissionEnum.INVENTORY_UPDATE)
    src_bal, dest_bal = await inventory_service.transfer_stock(tenant.organization_id, dto, actor_id=tenant.user_id)
    return [src_bal, dest_bal]


@router.get("/inventory/balances", response_model=List[InventoryBalanceResponseDTO])
async def list_balances(
    item_id: Optional[uuid.UUID] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[InventoryBalanceResponseDTO]:
    tenant.require_permission(PermissionEnum.INVENTORY_READ)
    return await inventory_service.list_balances(
        tenant.organization_id, item_id=item_id, location_id=location_id, limit=limit, offset=offset
    )
