"""Integration and Webhook application service."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from industrial_oracle.audit.application.service import AuditService, audit_service
from industrial_oracle.core.exceptions import EntityNotFoundException, BusinessRuleViolationException
from industrial_oracle.integrations.application.dtos import (
    EventQueryFilterDTO,
    OutboxEventDTO,
    OutboxRetryResponseDTO,
    WebhookCreateDTO,
    WebhookResponseDTO,
    WebhookUpdateDTO,
)
from industrial_oracle.integrations.application.interfaces import (
    IOutboxRepository,
    IWebhookRepository,
)
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint
from industrial_oracle.integrations.infrastructure.repository import (
    get_outbox_repository,
    get_webhook_repository,
    outbox_repository,
    webhook_repository,
)

logger = logging.getLogger("industrial_oracle.integrations.service")


class IntegrationService:
    """Orchestrates event inspection, outbox manual replay, and webhook endpoint governance."""

    def __init__(
        self,
        outbox_repo: Optional[IOutboxRepository] = None,
        webhook_repo: Optional[IWebhookRepository] = None,
        audit_svc: Optional[AuditService] = None,
    ) -> None:
        self.outbox_repo = outbox_repo or get_outbox_repository()
        self.webhook_repo = webhook_repo or get_webhook_repository()
        self.audit_svc = audit_svc or audit_service

    # ==========================================================================
    # Event & Outbox History Queries
    # ==========================================================================

    async def query_events(
        self,
        org_id: str,
        filter_dto: EventQueryFilterDTO,
    ) -> Tuple[List[OutboxEventDTO], int]:
        """Queries tenant events with strict tenant isolation and pagination."""
        offset = (max(1, filter_dto.page) - 1) * filter_dto.page_size
        events, total = await self.outbox_repo.query_events(
            organization_id=org_id,
            event_type=filter_dto.event_type,
            aggregate_type=filter_dto.aggregate_type,
            aggregate_id=filter_dto.aggregate_id,
            status=filter_dto.status,
            start_time=filter_dto.start_time,
            end_time=filter_dto.end_time,
            limit=filter_dto.page_size,
            offset=offset,
        )
        return [self._to_outbox_dto(ev) for ev in events], total

    async def get_event_by_id(self, event_identifier: str, org_id: str) -> OutboxEventDTO:
        """Finds event by event_id UUID or internal record ID within tenant boundary."""
        # Try finding by event_id first
        event = await self.outbox_repo.get_by_event_id(event_identifier, organization_id=org_id)
        if not event:
            # Fall back to internal ID
            event = await self.outbox_repo.get_by_id(event_identifier, organization_id=org_id)

        if not event or event.organization_id != str(org_id):
            raise EntityNotFoundException("IntegrationEvent", event_identifier)

        return self._to_outbox_dto(event)

    async def get_outbox_event(self, outbox_id: str, org_id: str) -> OutboxEventDTO:
        """Retrieves an outbox event by record ID scoped to the caller organization."""
        event = await self.outbox_repo.get_by_id(outbox_id, organization_id=org_id)
        if not event or event.organization_id != str(org_id):
            raise EntityNotFoundException("OutboxEvent", outbox_id)
        return self._to_outbox_dto(event)

    async def retry_outbox_event(
        self,
        outbox_id: str,
        org_id: str,
        actor_id: str,
    ) -> OutboxRetryResponseDTO:
        """Manually requeues a failed outbox event for processing (Admin/Replay)."""
        event = await self.outbox_repo.get_by_id(outbox_id, organization_id=org_id)
        if not event or event.organization_id != str(org_id):
            raise EntityNotFoundException("OutboxEvent", outbox_id)

        if event.status != OutboxStatus.FAILED:
            raise BusinessRuleViolationException(
                f"Cannot retry event in status '{event.status.value}'. Only FAILED events can be retried."
            )

        updated_event = await self.outbox_repo.retry(outbox_id, organization_id=org_id)

        # Record immutable audit log
        await self.audit_svc.log_action(
            organization_id=org_id,
            actor_id=actor_id,
            action="OUTBOX_EVENT_RETRY",
            target_entity="OutboxEvent",
            target_id=outbox_id,
            details={
                "event_id": updated_event.event_id,
                "event_type": updated_event.event_type,
                "previous_attempts": updated_event.attempts,
            },
        )

        return OutboxRetryResponseDTO(
            id=updated_event.id,
            event_id=updated_event.event_id,
            status=updated_event.status.value,
            attempts=updated_event.attempts,
            available_at=updated_event.available_at,
            message="Outbox event successfully requeued for background dispatch.",
        )

    # ==========================================================================
    # Webhook Management
    # ==========================================================================

    async def create_webhook(
        self,
        dto: WebhookCreateDTO,
        org_id: str,
        actor_id: str,
    ) -> WebhookResponseDTO:
        """Registers a new outbound webhook endpoint."""
        endpoint = WebhookEndpoint(
            organization_id=org_id,
            name=dto.name,
            url=dto.url,
            secret=dto.secret,
            subscribed_event_types=dto.subscribed_event_types or ["*"],
        )
        saved = await self.webhook_repo.create(endpoint)

        await self.audit_svc.log_action(
            organization_id=org_id,
            actor_id=actor_id,
            action="WEBHOOK_CREATED",
            target_entity="WebhookEndpoint",
            target_id=saved.id,
            details={
                "name": saved.name,
                "url": saved.url,
                "subscribed_event_types": saved.subscribed_event_types,
            },
        )
        return self._to_webhook_dto(saved)

    async def get_webhook(self, webhook_id: str, org_id: str) -> WebhookResponseDTO:
        """Retrieves a webhook endpoint configuration by ID within tenant boundary."""
        wh = await self.webhook_repo.get_by_id(webhook_id, organization_id=org_id)
        if not wh or wh.organization_id != str(org_id):
            raise EntityNotFoundException("WebhookEndpoint", webhook_id)
        return self._to_webhook_dto(wh)

    async def list_webhooks(self, org_id: str) -> List[WebhookResponseDTO]:
        """Lists all registered webhooks for the organization."""
        webhooks = await self.webhook_repo.list_by_org(org_id)
        return [self._to_webhook_dto(wh) for wh in webhooks]

    async def update_webhook(
        self,
        webhook_id: str,
        dto: WebhookUpdateDTO,
        org_id: str,
        actor_id: str,
    ) -> WebhookResponseDTO:
        """Updates webhook properties (name, url, subscribed events)."""
        wh = await self.webhook_repo.get_by_id(webhook_id, organization_id=org_id)
        if not wh or wh.organization_id != str(org_id):
            raise EntityNotFoundException("WebhookEndpoint", webhook_id)

        if dto.name is not None:
            wh.name = dto.name
        if dto.url is not None:
            wh.url = dto.url
        if dto.subscribed_event_types is not None:
            wh.subscribed_event_types = dto.subscribed_event_types

        updated = await self.webhook_repo.update(wh)
        await self.audit_svc.log_action(
            organization_id=org_id,
            actor_id=actor_id,
            action="WEBHOOK_UPDATED",
            target_entity="WebhookEndpoint",
            target_id=updated.id,
            details={"name": updated.name, "url": updated.url},
        )
        return self._to_webhook_dto(updated)

    async def activate_webhook(
        self,
        webhook_id: str,
        org_id: str,
        actor_id: str,
    ) -> WebhookResponseDTO:
        """Activates a deactivated webhook endpoint."""
        wh = await self.webhook_repo.get_by_id(webhook_id, organization_id=org_id)
        if not wh or wh.organization_id != str(org_id):
            raise EntityNotFoundException("WebhookEndpoint", webhook_id)

        wh.activate()
        updated = await self.webhook_repo.update(wh)
        await self.audit_svc.log_action(
            organization_id=org_id,
            actor_id=actor_id,
            action="WEBHOOK_ACTIVATED",
            target_entity="WebhookEndpoint",
            target_id=updated.id,
        )
        return self._to_webhook_dto(updated)

    async def deactivate_webhook(
        self,
        webhook_id: str,
        org_id: str,
        actor_id: str,
    ) -> WebhookResponseDTO:
        """Deactivates an active webhook endpoint."""
        wh = await self.webhook_repo.get_by_id(webhook_id, organization_id=org_id)
        if not wh or wh.organization_id != str(org_id):
            raise EntityNotFoundException("WebhookEndpoint", webhook_id)

        wh.deactivate()
        updated = await self.webhook_repo.update(wh)
        await self.audit_svc.log_action(
            organization_id=org_id,
            actor_id=actor_id,
            action="WEBHOOK_DEACTIVATED",
            target_entity="WebhookEndpoint",
            target_id=updated.id,
        )
        return self._to_webhook_dto(updated)

    async def delete_webhook(
        self,
        webhook_id: str,
        org_id: str,
        actor_id: str,
    ) -> bool:
        """Permanently deletes a webhook endpoint."""
        wh = await self.webhook_repo.get_by_id(webhook_id, organization_id=org_id)
        if not wh or wh.organization_id != str(org_id):
            raise EntityNotFoundException("WebhookEndpoint", webhook_id)

        deleted = await self.webhook_repo.delete(webhook_id, organization_id=org_id)
        if deleted:
            await self.audit_svc.log_action(
                organization_id=org_id,
                actor_id=actor_id,
                action="WEBHOOK_DELETED",
                target_entity="WebhookEndpoint",
                target_id=webhook_id,
            )
        return deleted

    # ==========================================================================
    # Helpers
    # ==========================================================================

    @staticmethod
    def _to_outbox_dto(ev: OutboxEvent) -> OutboxEventDTO:
        return OutboxEventDTO(
            id=ev.id,
            organization_id=ev.organization_id,
            event_id=ev.event_id,
            event_type=ev.event_type,
            aggregate_type=ev.aggregate_type,
            aggregate_id=ev.aggregate_id,
            payload=ev.payload,
            occurred_at=ev.occurred_at,
            created_at=ev.created_at,
            status=ev.status.value if hasattr(ev.status, "value") else str(ev.status),
            attempts=ev.attempts,
            available_at=ev.available_at,
            processed_at=ev.processed_at,
            last_error=ev.last_error,
            correlation_id=ev.correlation_id,
            causation_id=ev.causation_id,
            version=ev.version,
        )

    @staticmethod
    def _to_webhook_dto(wh: WebhookEndpoint) -> WebhookResponseDTO:
        return WebhookResponseDTO(
            id=wh.id,
            organization_id=wh.organization_id,
            name=wh.name,
            url=wh.url,
            active=wh.active,
            subscribed_event_types=wh.subscribed_event_types,
            created_at=wh.created_at,
            updated_at=wh.updated_at,
            secret=wh.masked_secret(),
        )


integration_service = IntegrationService()
