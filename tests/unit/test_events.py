"""Unit tests for domain events and internal event bus."""

import asyncio
import unittest
import uuid
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.domain.entity import AggregateRoot
from industrial_oracle.shared.infrastructure.event_bus import EventBus


class TestEvents(unittest.TestCase):
    def test_domain_event_envelope(self):
        org_id = str(uuid.uuid4())
        agg_id = str(uuid.uuid4())
        event = DomainEvent(
            event_type="MachineStarted",
            aggregate_id=agg_id,
            aggregate_type="Machine",
            organization_id=org_id,
            payload={"rpm": 1200, "temperature_c": 65.5},
        )
        self.assertIsNotNone(event.event_id)
        self.assertIsNotNone(event.occurred_at)
        self.assertEqual(event.event_type, "MachineStarted")
        self.assertEqual(event.aggregate_id, agg_id)
        self.assertEqual(event.payload["rpm"], 1200)

    def test_aggregate_root_event_collection(self):
        class OrderAggregate(AggregateRoot):
            def start(self, org_id: str):
                self.record_event(
                    DomainEvent(
                        event_type="WorkOrderStarted",
                        aggregate_id=str(self.id),
                        aggregate_type="WorkOrder",
                        organization_id=org_id,
                    )
                )

        agg = OrderAggregate()
        agg.start(org_id=str(uuid.uuid4()))
        events = agg.collect_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "WorkOrderStarted")

        # Second collection should be empty
        self.assertEqual(len(agg.collect_events()), 0)

    def test_event_bus_pub_sub(self):
        async def run():
            bus = EventBus()
            received = []

            async def handle_started(event: DomainEvent):
                received.append(event)

            bus.subscribe("MachineStarted", handle_started)

            event = DomainEvent(
                event_type="MachineStarted",
                aggregate_id="M-1",
                aggregate_type="Machine",
                organization_id="ORG-1",
            )
            await bus.publish(event)
            self.assertEqual(len(received), 1)
            self.assertEqual(received[0].aggregate_id, "M-1")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
