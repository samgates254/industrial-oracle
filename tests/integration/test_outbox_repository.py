"""Integration tests for Outbox repository operations, claim leases, and crash recovery."""

import asyncio
from datetime import datetime, timedelta, timezone
import unittest
import uuid

from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus
from industrial_oracle.integrations.infrastructure.repository import InMemoryOutboxRepository


class TestOutboxRepository(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryOutboxRepository()
        self.org_a = str(uuid.uuid4())
        self.org_b = str(uuid.uuid4())

    def test_append_and_query_by_id_tenant_scoped(self):
        async def run():
            ev = OutboxEvent(
                organization_id=self.org_a,
                event_type="WorkOrderCreated.v1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-1",
            )
            saved = await self.repo.append(ev)

            # Retrieve with matching org_id
            found = await self.repo.get_by_id(saved.id, organization_id=self.org_a)
            self.assertIsNotNone(found)
            self.assertEqual(found.id, saved.id)

            # Retrieve with different org_id returns None (strict tenant isolation)
            wrong_org = await self.repo.get_by_id(saved.id, organization_id=self.org_b)
            self.assertIsNone(wrong_org)

        asyncio.run(run())

    def test_claim_batch_fifo_order(self):
        async def run():
            now = datetime.now(timezone.utc)
            # Create two events at different times
            ev1 = OutboxEvent(
                organization_id=self.org_a,
                event_type="FirstEvent.v1",
                aggregate_type="Order",
                aggregate_id="1",
                occurred_at=(now - timedelta(seconds=10)).isoformat(),
                available_at=(now - timedelta(seconds=10)).isoformat(),
            )
            ev2 = OutboxEvent(
                organization_id=self.org_a,
                event_type="SecondEvent.v1",
                aggregate_type="Order",
                aggregate_id="2",
                occurred_at=now.isoformat(),
                available_at=now.isoformat(),
            )
            await self.repo.append(ev2)
            await self.repo.append(ev1)

            # Claim batch of size 1 should yield ev1 first (FIFO)
            claimed = await self.repo.claim_batch(batch_size=1, worker_id="worker-1", lease_seconds=30)
            self.assertEqual(len(claimed), 1)
            self.assertEqual(claimed[0].id, ev1.id)
            self.assertEqual(claimed[0].status, OutboxStatus.PROCESSING)

        asyncio.run(run())

    def test_claim_batch_skips_active_leased_events(self):
        async def run():
            ev = OutboxEvent(
                organization_id=self.org_a,
                event_type="TestEvent.v1",
                aggregate_type="Test",
                aggregate_id="1",
            )
            await self.repo.append(ev)

            # Worker 1 claims the event with 60s lease
            claimed_w1 = await self.repo.claim_batch(batch_size=10, worker_id="worker-1", lease_seconds=60)
            self.assertEqual(len(claimed_w1), 1)

            # Worker 2 attempts to claim while lease is active
            claimed_w2 = await self.repo.claim_batch(batch_size=10, worker_id="worker-2", lease_seconds=60)
            self.assertEqual(len(claimed_w2), 0)

        asyncio.run(run())

    def test_claim_batch_reclaims_expired_processing_lease(self):
        async def run():
            # Simulate an event locked by crashed worker with expired lease
            past_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
            ev = OutboxEvent(
                organization_id=self.org_a,
                event_type="TestEvent.v1",
                aggregate_type="Test",
                aggregate_id="1",
                status=OutboxStatus.PROCESSING,
                locked_by="crashed-worker",
                lock_expires_at=past_time,
            )
            await self.repo.append(ev)

            # New worker should safely reclaim the abandoned event
            reclaimed = await self.repo.claim_batch(batch_size=5, worker_id="survivor-worker", lease_seconds=30)
            self.assertEqual(len(reclaimed), 1)
            self.assertEqual(reclaimed[0].locked_by, "survivor-worker")
            self.assertEqual(reclaimed[0].status, OutboxStatus.PROCESSING)

        asyncio.run(run())

    def test_counts_and_oldest_pending_age(self):
        async def run():
            now = datetime.now(timezone.utc)
            ev_pending = OutboxEvent(
                organization_id=self.org_a,
                event_type="PendingEvent.v1",
                aggregate_type="Test",
                aggregate_id="1",
                occurred_at=(now - timedelta(seconds=40)).isoformat(),
            )
            ev_failed = OutboxEvent(
                organization_id=self.org_a,
                event_type="FailedEvent.v1",
                aggregate_type="Test",
                aggregate_id="2",
                status=OutboxStatus.FAILED,
            )
            await self.repo.append(ev_pending)
            await self.repo.append(ev_failed)

            pending_count = await self.repo.count_pending(self.org_a)
            failed_count = await self.repo.count_failed(self.org_a)
            age = await self.repo.get_oldest_pending_age_seconds(self.org_a)

            self.assertEqual(pending_count, 1)
            self.assertEqual(failed_count, 1)
            self.assertIsNotNone(age)
            self.assertGreaterEqual(age, 35.0)

        asyncio.run(run())

    def test_query_events_with_filters(self):
        async def run():
            ev1 = OutboxEvent(
                organization_id=self.org_a,
                event_type="WorkOrderCreated.v1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-10",
                status=OutboxStatus.PUBLISHED,
            )
            ev2 = OutboxEvent(
                organization_id=self.org_a,
                event_type="ProductionRunStarted.v1",
                aggregate_type="ProductionRun",
                aggregate_id="RUN-20",
                status=OutboxStatus.PENDING,
            )
            await self.repo.append(ev1)
            await self.repo.append(ev2)

            # Filter by aggregate_type
            res, total = await self.repo.query_events(self.org_a, aggregate_type="WorkOrder")
            self.assertEqual(total, 1)
            self.assertEqual(res[0].aggregate_id, "WO-10")

            # Filter by status
            res_pending, total_pending = await self.repo.query_events(self.org_a, status="PENDING")
            self.assertEqual(total_pending, 1)
            self.assertEqual(res_pending[0].aggregate_id, "RUN-20")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
