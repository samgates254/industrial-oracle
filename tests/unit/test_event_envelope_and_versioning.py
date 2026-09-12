"""Unit tests for EventEnvelope formatting, serialization, and schema versioning."""

import json
import unittest
import uuid

from industrial_oracle.integrations.domain.event_envelope import EventEnvelope
from industrial_oracle.shared.domain.events import DomainEvent


class TestEventEnvelopeAndVersioning(unittest.TestCase):
    def test_envelope_initialization_and_properties(self):
        org_id = str(uuid.uuid4())
        envelope = EventEnvelope(
            event_type="WorkOrderCreated",
            event_version="v1",
            organization_id=org_id,
            aggregate_type="WorkOrder",
            aggregate_id="WO-100",
            payload={"priority": "HIGH"},
            correlation_id="req-999",
            causation_id="cmd-888",
        )
        self.assertEqual(envelope.qualified_event_type, "WorkOrderCreated.v1")
        self.assertEqual(envelope.event_version, "v1")
        self.assertEqual(envelope.organization_id, org_id)
        self.assertEqual(envelope.aggregate_id, "WO-100")
        self.assertEqual(envelope.payload["priority"], "HIGH")
        self.assertEqual(envelope.correlation_id, "req-999")
        self.assertEqual(envelope.causation_id, "cmd-888")

    def test_envelope_serialization_and_deserialization(self):
        org_id = str(uuid.uuid4())
        original = EventEnvelope(
            event_type="ProductionRunStarted",
            event_version="v1",
            organization_id=org_id,
            aggregate_type="ProductionRun",
            aggregate_id="RUN-200",
            payload={"product_code": "PROD-A", "planned_quantity": 500.0},
        )
        json_str = original.to_json()
        restored = EventEnvelope.from_json(json_str)

        self.assertEqual(restored.event_id, original.event_id)
        self.assertEqual(restored.event_type, "ProductionRunStarted")
        self.assertEqual(restored.event_version, "v1")
        self.assertEqual(restored.qualified_event_type, "ProductionRunStarted.v1")
        self.assertEqual(restored.organization_id, org_id)
        self.assertEqual(restored.payload["planned_quantity"], 500.0)

    def test_from_domain_event_mapping(self):
        org_id = str(uuid.uuid4())
        domain_ev = DomainEvent(
            event_type="InventoryIssued",
            aggregate_id="BAL-300",
            aggregate_type="InventoryBalance",
            organization_id=org_id,
            payload={"item_id": "ITEM-1", "quantity": 25.0},
            event_version="v1",
            correlation_id="corr-abc",
            causation_id="caus-def",
        )

        envelope = EventEnvelope.from_domain_event(domain_ev)
        self.assertEqual(envelope.event_id, domain_ev.event_id)
        self.assertEqual(envelope.event_type, "InventoryIssued")
        self.assertEqual(envelope.qualified_event_type, "InventoryIssued.v1")
        self.assertEqual(envelope.correlation_id, "corr-abc")
        self.assertEqual(envelope.causation_id, "caus-def")
        self.assertEqual(envelope.payload["quantity"], 25.0)

    def test_event_version_parsing_compatibility(self):
        # Deserializing dictionary where event_type contains qualified dot notation
        raw_dict = {
            "event_id": str(uuid.uuid4()),
            "event_type": "MaterialConsumed.v1",
            "aggregate_type": "ProductionRun",
            "aggregate_id": "RUN-50",
            "organization_id": "ORG-1",
            "payload": {"consumed_qty": 10.0},
        }
        envelope = EventEnvelope.from_dict(raw_dict)
        self.assertEqual(envelope.event_type, "MaterialConsumed")
        self.assertEqual(envelope.event_version, "v1")
        self.assertEqual(envelope.qualified_event_type, "MaterialConsumed.v1")


if __name__ == "__main__":
    unittest.main()
