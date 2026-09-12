"""Application interfaces and contracts for outbox, events, webhooks, and external adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from industrial_oracle.integrations.domain.consumption import EventConsumption
from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.integrations.domain.outbox import OutboxEvent
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint


class IOutboxRepository(ABC):
    """Repository interface for persisting, querying, claiming, and updating outbox events."""

    @abstractmethod
    async def append(self, outbox_event: OutboxEvent) -> OutboxEvent:
        """Appends a new outbox event record within the ongoing transactional context."""
        pass

    @abstractmethod
    async def get_by_id(self, id: str, organization_id: Optional[str] = None) -> Optional[OutboxEvent]:
        """Retrieves an outbox event by its internal primary key, enforcing tenant isolation."""
        pass

    @abstractmethod
    async def get_by_event_id(self, event_id: str, organization_id: Optional[str] = None) -> Optional[OutboxEvent]:
        """Retrieves an outbox event by its global event UUID, enforcing tenant isolation."""
        pass

    @abstractmethod
    async def claim_batch(
        self,
        batch_size: int,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> List[OutboxEvent]:
        """Safely claims a batch of pending or expired processing events for publishing.

        Must prevent race conditions across multiple concurrent worker instances.
        """
        pass

    @abstractmethod
    async def mark_published(self, id: str, processed_at: Optional[str] = None) -> None:
        """Marks a claimed event as successfully published."""
        pass

    @abstractmethod
    async def mark_failed(
        self,
        id: str,
        error: str,
        next_available_at: Optional[str] = None,
        max_attempts: int = 3,
    ) -> None:
        """Records an execution error on an outbox event, scheduling retry or marking FAILED."""
        pass

    @abstractmethod
    async def retry(self, id: str, organization_id: str) -> OutboxEvent:
        """Manually requeues a FAILED event for immediate reprocessing."""
        pass

    @abstractmethod
    async def count_pending(self, organization_id: Optional[str] = None) -> int:
        """Returns count of pending outbox events."""
        pass

    @abstractmethod
    async def count_failed(self, organization_id: Optional[str] = None) -> int:
        """Returns count of failed outbox events."""
        pass

    @abstractmethod
    async def get_oldest_pending_age_seconds(self, organization_id: Optional[str] = None) -> Optional[float]:
        """Returns the age in seconds of the oldest pending event, or None if queue is empty."""
        pass

    @abstractmethod
    async def query_events(
        self,
        organization_id: str,
        event_type: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[OutboxEvent], int]:
        """Queries tenant-scoped outbox event history with filtering and pagination."""
        pass


class IEventConsumptionRepository(ABC):
    """Repository interface for enforcing consumer idempotency and tracking event deliveries."""

    @abstractmethod
    async def has_consumed(self, consumer_name: str, event_id: str) -> bool:
        """Returns True if consumer has already processed the specified event."""
        pass

    @abstractmethod
    async def record_consumption(self, consumption: EventConsumption) -> bool:
        """Records an event consumption record. Returns True if recorded, False if already exists."""
        pass

    @abstractmethod
    async def get_consumption(self, consumer_name: str, event_id: str) -> Optional[EventConsumption]:
        """Retrieves consumption record for auditing/inspection."""
        pass


class IWebhookRepository(ABC):
    """Repository interface for managing tenant webhook configurations."""

    @abstractmethod
    async def create(self, webhook: WebhookEndpoint) -> WebhookEndpoint:
        """Registers a new webhook endpoint."""
        pass

    @abstractmethod
    async def get_by_id(self, id: str, organization_id: Optional[str] = None) -> Optional[WebhookEndpoint]:
        """Retrieves a webhook endpoint by ID, scoped to organization."""
        pass

    @abstractmethod
    async def list_by_org(self, organization_id: str) -> List[WebhookEndpoint]:
        """Lists all registered webhook endpoints for an organization."""
        pass

    @abstractmethod
    async def update(self, webhook: WebhookEndpoint) -> WebhookEndpoint:
        """Updates webhook configuration."""
        pass

    @abstractmethod
    async def delete(self, id: str, organization_id: str) -> bool:
        """Deletes a webhook endpoint."""
        pass

    @abstractmethod
    async def find_subscribers(self, organization_id: str, event_type: str) -> List[WebhookEndpoint]:
        """Finds active webhooks registered for the given event type within an organization."""
        pass


class IEventPublisher(ABC):
    """Abstract publisher interface for dispatching canonical event envelopes."""

    @abstractmethod
    async def publish(self, envelope: EventEnvelope) -> bool:
        """Dispatches an event envelope to internal handlers or external broker adapters.

        Returns True on successful delivery/acceptance, False on transient failure.
        """
        pass


class IERPAdapter(ABC):
    """Integration contract for external Enterprise Resource Planning (ERP) systems."""

    @abstractmethod
    async def sync_work_order(self, work_order_id: str, payload: Dict[str, Any]) -> bool:
        """Propagates work order lifecycle status to an external ERP system."""
        pass

    @abstractmethod
    async def sync_inventory_transaction(self, transaction_id: str, payload: Dict[str, Any]) -> bool:
        """Synchronizes inventory stock movements with an external ERP system."""
        pass


class IWebhookAdapter(ABC):
    """Integration contract for dispatching outbound HTTP webhook notifications."""

    @abstractmethod
    async def deliver(self, webhook: WebhookEndpoint, envelope: EventEnvelope) -> bool:
        """Delivers a webhook notification with HMAC-SHA256 signature and retry safety."""
        pass
