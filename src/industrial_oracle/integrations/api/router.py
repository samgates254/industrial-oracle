"""FastAPI routes for Outbox events, event history queries, replay, and webhooks."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, status

from industrial_oracle.core.security import (
    PermissionEnum,
    TenantContext,
    get_tenant_context,
)
from industrial_oracle.integrations.application.dtos import (
    EventQueryFilterDTO,
    OutboxEventDTO,
    OutboxRetryResponseDTO,
    WebhookCreateDTO,
    WebhookResponseDTO,
    WebhookUpdateDTO,
)
from industrial_oracle.integrations.application.services import (
    IntegrationService,
    integration_service,
)

router = APIRouter(prefix="/api/v1/integration", tags=["Integration & Events"])


# ==============================================================================
# 1. Events Query Endpoints
# ==============================================================================

@router.get(
    "/events",
    response_model=Dict[str, Any],
    summary="Query historical events",
)
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    aggregate_type: Optional[str] = Query(None, description="Filter by aggregate type"),
    aggregate_id: Optional[str] = Query(None, description="Filter by aggregate id"),
    status: Optional[str] = Query(None, description="Filter by outbox status"),
    start_time: Optional[str] = Query(None, description="ISO 8601 start timestamp"),
    end_time: Optional[str] = Query(None, description="ISO 8601 end timestamp"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    filter_dto = EventQueryFilterDTO(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    items, total = await integration_service.query_events(tenant.org_id, filter_dto)
    return {
        "items": [item.dict() if hasattr(item, "dict") else item.__dict__ for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/events/{id}",
    response_model=OutboxEventDTO,
    summary="Get single event details",
)
async def get_event(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> OutboxEventDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    return await integration_service.get_event_by_id(id, tenant.org_id)


# ==============================================================================
# 2. Outbox Management & Replay Endpoints
# ==============================================================================

@router.get(
    "/outbox",
    response_model=Dict[str, Any],
    summary="List operational outbox records",
)
async def list_outbox(
    status: Optional[str] = Query(None, description="Filter by outbox status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    filter_dto = EventQueryFilterDTO(
        status=status,
        page=page,
        page_size=page_size,
    )
    items, total = await integration_service.query_events(tenant.org_id, filter_dto)
    return {
        "items": [item.dict() if hasattr(item, "dict") else item.__dict__ for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/outbox/{id}",
    response_model=OutboxEventDTO,
    summary="Get single outbox record",
)
async def get_outbox_record(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> OutboxEventDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    return await integration_service.get_outbox_event(id, tenant.org_id)


@router.post(
    "/outbox/{id}/retry",
    response_model=OutboxRetryResponseDTO,
    summary="Manually retry/requeue a failed outbox event",
)
async def retry_outbox_event(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> OutboxRetryResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_RETRY)
    return await integration_service.retry_outbox_event(
        outbox_id=id,
        org_id=tenant.org_id,
        actor_id=tenant.user_id,
    )


# ==============================================================================
# 3. Webhook Endpoints
# ==============================================================================

@router.post(
    "/webhooks",
    response_model=WebhookResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new webhook endpoint",
)
async def create_webhook(
    dto: WebhookCreateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WebhookResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_MANAGE)
    return await integration_service.create_webhook(dto, tenant.org_id, tenant.user_id)


@router.get(
    "/webhooks",
    response_model=List[WebhookResponseDTO],
    summary="List registered webhooks",
)
async def list_webhooks(
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[WebhookResponseDTO]:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    return await integration_service.list_webhooks(tenant.org_id)


@router.get(
    "/webhooks/{id}",
    response_model=WebhookResponseDTO,
    summary="Get webhook endpoint details",
)
async def get_webhook(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WebhookResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_READ)
    return await integration_service.get_webhook(id, tenant.org_id)


@router.patch(
    "/webhooks/{id}",
    response_model=WebhookResponseDTO,
    summary="Update webhook endpoint configuration",
)
async def update_webhook(
    id: str,
    dto: WebhookUpdateDTO,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WebhookResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_MANAGE)
    return await integration_service.update_webhook(id, dto, tenant.org_id, tenant.user_id)


@router.post(
    "/webhooks/{id}/activate",
    response_model=WebhookResponseDTO,
    summary="Activate a webhook endpoint",
)
async def activate_webhook(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WebhookResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_MANAGE)
    return await integration_service.activate_webhook(id, tenant.org_id, tenant.user_id)


@router.post(
    "/webhooks/{id}/deactivate",
    response_model=WebhookResponseDTO,
    summary="Deactivate a webhook endpoint",
)
async def deactivate_webhook(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> WebhookResponseDTO:
    tenant.require_permission(PermissionEnum.INTEGRATION_MANAGE)
    return await integration_service.deactivate_webhook(id, tenant.org_id, tenant.user_id)


@router.delete(
    "/webhooks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook endpoint",
)
async def delete_webhook(
    id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> Response:
    tenant.require_permission(PermissionEnum.INTEGRATION_MANAGE)
    await integration_service.delete_webhook(id, tenant.org_id, tenant.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
