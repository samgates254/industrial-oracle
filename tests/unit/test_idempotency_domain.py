"""Unit tests for EventConsumption idempotency and WebhookEndpoint filtering."""

import asyncio
import unittest
import uuid

from industrial_oracle.integrations.domain.consumption import EventConsumption
from industrial_oracle.integrations.domain.webhook import WebhookEndpoint
from industrial_oracle.integrations.infrastructure.repository import InMemoryEventConsumptionRepository


class TestIdempotencyDomain(unittest.TestCase):
    def test_event_consumption_entity_lifecycle(self):
        ev_id = str(uuid.uuid4())
        consumption = EventConsumption(
            consumer_name="analytics_pipeline",
            event_id=ev_id,
            status="SUCCESS",
        )
        self.assertEqual(consumption.consumer_name, "analytics_pipeline")
        self.assertEqual(consumption.event_id, ev_id)
        self.assertEqual(consumption.status, "SUCCESS")
        self.assertIsNone(consumption.error)
        self.assertIsNotNone(consumption.consumed_at)

    def test_in_memory_consumption_repository_deduplication(self):
        async def run():
            repo = InMemoryEventConsumptionRepository()
            ev_id = str(uuid.uuid4())
            c1 = EventConsumption(consumer_name="erp_syncer", event_id=ev_id)

            # First consumption record succeeds
            first_res = await repo.record_consumption(c1)
            self.assertTrue(first_res)
            self.assertTrue(await repo.has_consumed("erp_syncer", ev_id))

            # Second consumption record with same consumer and event is rejected
            c2 = EventConsumption(consumer_name="erp_syncer", event_id=ev_id)
            second_res = await repo.record_consumption(c2)
            self.assertFalse(second_res)

            # Different consumer can process the same event
            c3 = EventConsumption(consumer_name="audit_indexer", event_id=ev_id)
            third_res = await repo.record_consumption(c3)
            self.assertTrue(third_res)

        asyncio.run(run())

    def test_webhook_endpoint_matching_and_secret_masking(self):
        wh = WebhookEndpoint(
            organization_id=str(uuid.uuid4()),
            name="SAP ERP Sync",
            url="https://erp.example.com/hooks",
            secret="whsec_1234567890abcdef1234567890abcdef",
            subscribed_event_types=["WorkOrder*.v1", "MaterialConsumed.v1"],
        )

        # Matching tests
        self.assertTrue(wh.matches_event("WorkOrderCompleted.v1"))
        self.assertTrue(wh.matches_event("WorkOrderReleased.v1"))
        self.assertTrue(wh.matches_event("MaterialConsumed.v1"))
        self.assertFalse(wh.matches_event("ProductionRunStarted.v1"))

        # Secret masking test
        masked = wh.masked_secret()
        self.assertTrue(masked.startswith("whsec_"))
        self.assertIn("****", masked)
        self.assertNotIn("1234567890abcdef", masked)

        # Deactivated endpoint matches nothing
        wh.deactivate()
        self.assertFalse(wh.matches_event("WorkOrderCompleted.v1"))


if __name__ == "__main__":
    unittest.main()
