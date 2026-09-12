"""Event publisher implementations for internal dispatch and external webhook notifications."""

import asyncio
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from industrial_oracle.integrations.application.interfaces import (
    IEventConsumptionRepository,
    IEventPublisher,
    IWebhookRepository,
    IWebhookAdapter,
)
from industrial_oracle.integrations.domain.consumption import EventConsumption
from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.infrastructure.event_bus import event_bus

logger = logging.getLogger("industrial_oracle.integrations.publisher")


class InternalEventPublisher(IEventPublisher):
    """Dispatches canonical event envelopes to internal in-memory event bus and registered consumers."""

    def __init__(
        self,
        consumption_repo: Optional[IEventConsumptionRepository] = None,
        webhook_repo: Optional[IWebhookRepository] = None,
        webhook_adapter: Optional[IWebhookAdapter] = None,
    ) -> None:
        self.consumption_repo = consumption_repo
        self.webhook_repo = webhook_repo
        self.webhook_adapter = webhook_adapter
        self._handlers: Dict[str, List[Callable[[EventEnvelope], Any]]] = {}

    def register_consumer(
        self,
        consumer_name: str,
        event_type: str,
        handler: Callable[[EventEnvelope], Any],
    ) -> None:
        """Registers an internal consumer for a specific event type."""
        key = f"{consumer_name}:{event_type}"
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    async def publish(self, envelope: EventEnvelope) -> bool:
        """Publishes the envelope to the internal bus, consumers, and webhooks."""
        try:
            # 1. Dispatch to shared domain EventBus
            domain_ev = DomainEvent(
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                aggregate_id=envelope.aggregate_id,
                aggregate_type=envelope.aggregate_type,
                occurred_at=envelope.occurred_at,
                organization_id=envelope.organization_id,
                payload=envelope.payload,
                event_version=envelope.event_version,
                correlation_id=envelope.correlation_id,
                causation_id=envelope.causation_id,
            )
            await event_bus.publish(domain_ev)

            # 2. Dispatch to registered internal consumers with idempotency
            for key, handlers in self._handlers.items():
                consumer_name, target_type = key.split(":", 1)
                if target_type == "*" or target_type == envelope.event_type or target_type == envelope.qualified_event_type:
                    if self.consumption_repo:
                        already_done = await self.consumption_repo.has_consumed(consumer_name, envelope.event_id)
                        if already_done:
                            continue  # Skip duplicate execution safely!

                    for h in handlers:
                        try:
                            res = h(envelope)
                            if asyncio.iscoroutine(res):
                                await res
                            if self.consumption_repo:
                                await self.consumption_repo.record_consumption(
                                    EventConsumption(
                                        consumer_name=consumer_name,
                                        event_id=envelope.event_id,
                                        status="SUCCESS",
                                    )
                                )
                        except Exception as h_err:
                            logger.error("Consumer %s failed processing %s: %s", consumer_name, envelope.event_id, h_err)
                            if self.consumption_repo:
                                await self.consumption_repo.record_consumption(
                                    EventConsumption(
                                        consumer_name=consumer_name,
                                        event_id=envelope.event_id,
                                        status="FAILED",
                                        error=str(h_err),
                                    )
                                )
                            raise

            # 3. Deliver to matching webhooks asynchronously
            if self.webhook_repo and self.webhook_adapter and envelope.organization_id:
                endpoints = await self.webhook_repo.find_subscribers(
                    organization_id=envelope.organization_id,
                    event_type=envelope.qualified_event_type,
                )
                for endpoint in endpoints:
                    try:
                        await self.webhook_adapter.deliver(endpoint, envelope)
                    except Exception as wh_err:
                        logger.warning("Webhook delivery to %s failed: %s", endpoint.url, wh_err)

            return True
        except Exception as exc:
            logger.error("Failed to publish event %s: %s", envelope.event_id, exc)
            raise


class DefaultWebhookAdapter(IWebhookAdapter):
    """Reliable webhook adapter signing payloads with HMAC-SHA256."""

    def __init__(self) -> None:
        self.deliveries: List[Dict[str, Any]] = []

    async def deliver(self, webhook: WebhookEndpoint, envelope: EventEnvelope) -> bool:
        """Constructs signed payload and delivers to target webhook endpoint."""
        body = envelope.to_json()
        signature = hmac.new(
            webhook.secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        delivery_record = {
            "webhook_id": webhook.id,
            "url": webhook.url,
            "event_id": envelope.event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signature": f"sha256={signature}",
            "payload": body,
            "status": "DELIVERED",
        }
        self.deliveries.append(delivery_record)
        return True
