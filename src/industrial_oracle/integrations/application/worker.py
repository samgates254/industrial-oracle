"""Outbox background worker implementation for durable event dispatching."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional
import uuid

from industrial_oracle.integrations.application.interfaces import IEventPublisher, IOutboxRepository
from industrial_oracle.integrations.infrastructure.repository import get_outbox_repository
from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.integrations.domain.retry_policy import RetryPolicy

logger = logging.getLogger("industrial_oracle.integrations.worker")


class OutboxWorker:
    """Asynchronous worker responsible for polling, claiming, and dispatching outbox events."""

    def __init__(
        self,
        publisher: IEventPublisher,
        outbox_repo: Optional[IOutboxRepository] = None,
        worker_id: Optional[str] = None,
        batch_size: int = 10,
        lease_seconds: int = 30,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self.outbox_repo = outbox_repo or get_outbox_repository()
        self.publisher = publisher
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.batch_size = max(1, batch_size)
        self.lease_seconds = max(5, lease_seconds)
        self.retry_policy = retry_policy or RetryPolicy()
        self._is_running = False

    async def process_batch(self) -> int:
        """Fetches and processes a batch of claimable outbox events."""
        events = await self.outbox_repo.claim_batch(
            batch_size=self.batch_size,
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
        )

        if not events:
            return 0

        published_count = 0
        for event in events:
            envelope = EventEnvelope(
                event_id=event.event_id,
                event_type=event.event_type,
                event_version="v1",
                occurred_at=event.occurred_at,
                organization_id=event.organization_id,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                payload=event.payload,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
            )

            try:
                success = await self.publisher.publish(envelope)
                if success:
                    await self.outbox_repo.mark_published(event.id)
                    published_count += 1
                else:
                    raise RuntimeError("Publisher failed to deliver event envelope.")
            except Exception as exc:
                err_msg = str(exc)
                logger.warning(
                    "Worker %s failed to dispatch outbox event %s (attempt %d): %s",
                    self.worker_id,
                    event.id,
                    event.attempts,
                    err_msg,
                )

                if self.retry_policy.should_retry(event.attempts):
                    next_avail = self.retry_policy.calculate_next_available_at(event.attempts)
                    await self.outbox_repo.mark_failed(
                        id=event.id,
                        error=err_msg,
                        next_available_at=next_avail.isoformat(),
                        max_attempts=self.retry_policy.max_attempts,
                    )
                else:
                    await self.outbox_repo.mark_failed(
                        id=event.id,
                        error=f"Max attempts ({self.retry_policy.max_attempts}) exhausted: {err_msg}",
                        next_available_at=None,
                        max_attempts=self.retry_policy.max_attempts,
                    )

        return published_count

    async def run_once(self) -> int:
        """Executes a single processing iteration."""
        return await self.process_batch()

    async def run_forever(self, poll_interval: float = 1.0, stop_event: Optional[asyncio.Event] = None) -> None:
        """Continuous polling execution loop with graceful shutdown support."""
        self._is_running = True
        logger.info("Outbox worker %s started with poll_interval=%.2fs", self.worker_id, poll_interval)

        while self._is_running:
            if stop_event and stop_event.is_set():
                break
            try:
                count = await self.process_batch()
                if count == 0:
                    await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Outbox worker %s encountered loop error: %s", self.worker_id, e)
                await asyncio.sleep(poll_interval)

        self._is_running = False
        logger.info("Outbox worker %s stopped gracefully.", self.worker_id)

    def stop(self) -> None:
        """Signals the worker loop to terminate."""
        self._is_running = False
