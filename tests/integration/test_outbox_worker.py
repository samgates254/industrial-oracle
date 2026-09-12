"""Integration tests for OutboxWorker execution, retries, and concurrent processing."""

import asyncio
from datetime import datetime, timedelta, timezone
import unittest
import uuid

from industrial_oracle.integrations.application.worker import OutboxWorker
from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.domain.retry_policy import RetryPolicy
from industrial_oracle.integrations.infrastructure.publisher import InternalEventPublisher
from industrial_oracle.integrations.infrastructure.repository import InMemoryOutboxRepository


class TestOutboxWorker(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryOutboxRepository()
        self.publisher = InternalEventPublisher()
        self.worker = OutboxWorker(
            outbox_repo=self.repo,
            publisher=self.publisher,
            worker_id="test-worker",
            batch_size=10,
            lease_seconds=30,
            retry_policy=RetryPolicy(max_attempts=3, base_backoff_seconds=0.1),
        )
        self.org_id = str(uuid.uuid4())

    def test_worker_successful_dispatch_and_publish(self):
        async def run():
            received = []
            self.publisher.register_consumer("test_consumer", "WorkOrderCreated.v1", lambda env: received.append(env))

            ev = OutboxEvent(
                organization_id=self.org_id,
                event_type="WorkOrderCreated.v1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-99",
                payload={"priority": "HIGH"},
            )
            await self.repo.append(ev)

            # Worker processes batch
            processed = await self.worker.process_batch()
            self.assertEqual(processed, 1)

            # Verify published status
            stored = await self.repo.get_by_id(ev.id)
            self.assertEqual(stored.status, OutboxStatus.PUBLISHED)
            self.assertIsNotNone(stored.processed_at)
            self.assertEqual(len(received), 1)
            self.assertEqual(received[0].aggregate_id, "WO-99")

        asyncio.run(run())

    def test_worker_transient_failure_exponential_backoff(self):
        async def run():
            # Register failing consumer
            def failing_consumer(env):
                raise ConnectionError("Simulated remote network dropout")

            self.publisher.register_consumer("flaky_consumer", "InventoryAdjusted.v1", failing_consumer)

            ev = OutboxEvent(
                organization_id=self.org_id,
                event_type="InventoryAdjusted.v1",
                aggregate_type="InventoryBalance",
                aggregate_id="BAL-1",
            )
            await self.repo.append(ev)

            # First attempt fails
            processed = await self.worker.process_batch()
            self.assertEqual(processed, 0)

            stored = await self.repo.get_by_id(ev.id)
            self.assertEqual(stored.attempts, 1)
            self.assertEqual(stored.status, OutboxStatus.PENDING)
            self.assertIn("Simulated remote network dropout", stored.last_error)
            self.assertIsNotNone(stored.available_at)

        asyncio.run(run())

    def test_worker_exhaustion_moves_to_failed_dead_letter(self):
        async def run():
            def failing_consumer(env):
                raise RuntimeError("Unrecoverable data corruption")

            self.publisher.register_consumer("doomed_consumer", "CriticalEvent.v1", failing_consumer)

            ev = OutboxEvent(
                organization_id=self.org_id,
                event_type="CriticalEvent.v1",
                aggregate_type="Asset",
                aggregate_id="AST-1",
            )
            await self.repo.append(ev)

            # Execute 3 iterations
            for _ in range(3):
                # Set available_at to past so worker claims it immediately
                ev_cur = await self.repo.get_by_id(ev.id)
                ev_cur.available_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
                await self.worker.process_batch()

            final = await self.repo.get_by_id(ev.id)
            self.assertEqual(final.attempts, 3)
            self.assertEqual(final.status, OutboxStatus.FAILED)
            self.assertIn("Max attempts (3) exhausted", final.last_error)

        asyncio.run(run())

    def test_worker_recovers_crashed_worker_lease(self):
        async def run():
            # An event left in PROCESSING by a worker that crashed 60s ago
            past_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
            ev = OutboxEvent(
                organization_id=self.org_id,
                event_type="WorkOrderReleased.v1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-50",
                status=OutboxStatus.PROCESSING,
                locked_by="crashed-worker-99",
                lock_expires_at=past_time,
            )
            await self.repo.append(ev)

            # Worker processes batch and reclaims
            processed = await self.worker.process_batch()
            self.assertEqual(processed, 1)

            final = await self.repo.get_by_id(ev.id)
            self.assertEqual(final.status, OutboxStatus.PUBLISHED)

        asyncio.run(run())

    def test_concurrent_workers_no_duplicate_claims(self):
        async def run():
            # Seed 20 outbox events
            for i in range(20):
                ev = OutboxEvent(
                    organization_id=self.org_id,
                    event_type="BatchEvent.v1",
                    aggregate_type="Item",
                    aggregate_id=f"ITEM-{i}",
                )
                await self.repo.append(ev)

            w1 = OutboxWorker(outbox_repo=self.repo, publisher=self.publisher, worker_id="w1", batch_size=10)
            w2 = OutboxWorker(outbox_repo=self.repo, publisher=self.publisher, worker_id="w2", batch_size=10)

            # Run both workers concurrently
            res1, res2 = await asyncio.gather(w1.process_batch(), w2.process_batch())

            # All 20 events should be processed across the two workers with zero collision
            self.assertEqual(res1 + res2, 20)
            pending = await self.repo.count_pending(self.org_id)
            self.assertEqual(pending, 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
