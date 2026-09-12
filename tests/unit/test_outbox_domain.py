"""Unit tests for OutboxEvent domain entity, state machine, and invariants."""

from datetime import datetime, timedelta, timezone
import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.integrations.domain.outbox import OutboxEvent, OutboxStatus


class TestOutboxDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = str(uuid.uuid4())
        self.event_id = str(uuid.uuid4())
        self.event = OutboxEvent(
            organization_id=self.org_id,
            event_id=self.event_id,
            event_type="WorkOrderCompleted.v1",
            aggregate_type="WorkOrder",
            aggregate_id="WO-001",
            payload={"work_order_number": "WO-2026-001", "status": "COMPLETED"},
            correlation_id="corr-123",
            causation_id="caus-456",
        )

    def test_outbox_event_initial_state(self):
        self.assertIsNotNone(self.event.id)
        self.assertEqual(self.event.status, OutboxStatus.PENDING)
        self.assertEqual(self.event.attempts, 0)
        self.assertEqual(self.event.version, 1)
        self.assertIsNone(self.event.processed_at)
        self.assertIsNone(self.event.last_error)
        self.assertIsNone(self.event.locked_by)
        self.assertIsNone(self.event.lock_expires_at)
        self.assertEqual(self.event.correlation_id, "corr-123")
        self.assertEqual(self.event.causation_id, "caus-456")

    def test_outbox_event_mark_processing(self):
        worker_id = "worker-alpha"
        self.event.mark_processing(worker_id=worker_id, lease_seconds=45)

        self.assertEqual(self.event.status, OutboxStatus.PROCESSING)
        self.assertEqual(self.event.locked_by, worker_id)
        self.assertEqual(self.event.attempts, 1)
        self.assertEqual(self.event.version, 2)
        self.assertIsNotNone(self.event.lock_expires_at)
        self.assertFalse(self.event.is_lock_expired())

    def test_outbox_event_mark_published(self):
        self.event.mark_processing(worker_id="worker-alpha", lease_seconds=30)
        self.event.mark_published()

        self.assertEqual(self.event.status, OutboxStatus.PUBLISHED)
        self.assertIsNotNone(self.event.processed_at)
        self.assertIsNone(self.event.locked_by)
        self.assertIsNone(self.event.lock_expires_at)
        self.assertEqual(self.event.version, 3)

        # Idempotent call should not raise
        self.event.mark_published()
        self.assertEqual(self.event.status, OutboxStatus.PUBLISHED)

    def test_outbox_event_cannot_claim_published_event(self):
        self.event.mark_published()
        with self.assertRaises(BusinessRuleViolationException):
            self.event.mark_processing("worker-beta")

    def test_outbox_event_mark_failed_retries(self):
        self.event.mark_processing(worker_id="worker-alpha")
        next_avail = (datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat()
        self.event.mark_failed(error="Connection timeout", next_available_at=next_avail, max_attempts=3)

        # Attempts is 1 < 3 -> should revert to PENDING
        self.assertEqual(self.event.status, OutboxStatus.PENDING)
        self.assertEqual(self.event.available_at, next_avail)
        self.assertEqual(self.event.last_error, "Connection timeout")
        self.assertIsNone(self.event.locked_by)

    def test_outbox_event_mark_failed_dead_letter(self):
        # Exhaust 3 attempts
        for _ in range(3):
            self.event.mark_processing(worker_id="worker-alpha")
            self.event.mark_failed(error="Persistent broker rejection", max_attempts=3)

        # 3 attempts reached -> must transition to FAILED
        self.assertEqual(self.event.attempts, 3)
        self.assertEqual(self.event.status, OutboxStatus.FAILED)
        self.assertIn("Persistent broker rejection", self.event.last_error)

    def test_outbox_event_retry_from_failed(self):
        self.event.status = OutboxStatus.FAILED
        self.event.attempts = 3
        self.event.retry()

        self.assertEqual(self.event.status, OutboxStatus.PENDING)
        self.assertIsNotNone(self.event.available_at)
        self.assertIsNone(self.event.locked_by)

    def test_outbox_event_retry_rejected_if_not_failed(self):
        self.assertEqual(self.event.status, OutboxStatus.PENDING)
        with self.assertRaises(BusinessRuleViolationException):
            self.event.retry()

    def test_lock_expiration_evaluation(self):
        self.event.mark_processing(worker_id="worker-alpha", lease_seconds=10)
        self.assertFalse(self.event.is_lock_expired())

        # Simulate time passage beyond lease expiration
        future_time = datetime.now(timezone.utc) + timedelta(seconds=20)
        self.assertTrue(self.event.is_lock_expired(current_time=future_time))


if __name__ == "__main__":
    unittest.main()
