"""Integration tests for Idempotent Consumer pattern and duplicate event deduplication."""

import asyncio
import unittest
import uuid

from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.integrations.infrastructure.publisher import InternalEventPublisher
from industrial_oracle.integrations.infrastructure.repository import InMemoryEventConsumptionRepository


class TestIdempotentConsumer(unittest.TestCase):
    def setUp(self):
        self.consumption_repo = InMemoryEventConsumptionRepository()
        self.publisher = InternalEventPublisher(consumption_repo=self.consumption_repo)

    def test_consumer_executes_on_first_delivery(self):
        async def run():
            executed = []

            def handle_event(env: EventEnvelope):
                executed.append(env.event_id)

            self.publisher.register_consumer("billing_service", "WorkOrderCompleted.v1", handle_event)

            envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="WorkOrderCompleted",
                event_version="v1",
                organization_id="ORG-1",
                aggregate_type="WorkOrder",
                aggregate_id="WO-1",
            )

            await self.publisher.publish(envelope)
            self.assertEqual(len(executed), 1)
            self.assertEqual(executed[0], envelope.event_id)

            has_consumed = await self.consumption_repo.has_consumed("billing_service", envelope.event_id)
            self.assertTrue(has_consumed)

        asyncio.run(run())

    def test_consumer_skips_side_effect_on_duplicate_delivery(self):
        async def run():
            counter = {"count": 0}

            def handle_event(env: EventEnvelope):
                counter["count"] += 1

            self.publisher.register_consumer("inventory_adjuster", "InventoryIssued.v1", handle_event)

            envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="InventoryIssued",
                event_version="v1",
                organization_id="ORG-1",
                aggregate_type="InventoryBalance",
                aggregate_id="BAL-1",
            )

            # First delivery
            await self.publisher.publish(envelope)
            self.assertEqual(counter["count"], 1)

            # Duplicate delivery of identical event_id
            await self.publisher.publish(envelope)
            # Counter MUST remain 1 — side effect was safely not executed twice!
            self.assertEqual(counter["count"], 1)

        asyncio.run(run())

    def test_consumer_records_failure_status_on_error(self):
        async def run():
            def failing_handler(env: EventEnvelope):
                raise ValueError("Bad payload content")

            self.publisher.register_consumer("strict_consumer", "TestFailed.v1", failing_handler)

            envelope = EventEnvelope(
                event_id=str(uuid.uuid4()),
                event_type="TestFailed",
                event_version="v1",
                organization_id="ORG-1",
                aggregate_type="Test",
                aggregate_id="T-1",
            )

            with self.assertRaises(ValueError):
                await self.publisher.publish(envelope)

            rec = await self.consumption_repo.get_consumption("strict_consumer", envelope.event_id)
            self.assertIsNotNone(rec)
            self.assertEqual(rec.status, "FAILED")
            self.assertIn("Bad payload content", rec.error)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
