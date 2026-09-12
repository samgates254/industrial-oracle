"""Unit tests for TelemetryPoint domain entity."""

import unittest
import uuid
from datetime import datetime, timezone

from industrial_oracle.assets.domain.models import TelemetryPoint


class TestTelemetryPointDomain(unittest.TestCase):
    def test_telemetry_sampling(self):
        point = TelemetryPoint(
            organization_id=uuid.uuid4(),
            machine_id=uuid.uuid4(),
            metric_name="bearing_vibration",
            unit="mm/s",
            min_threshold=0.5,
            max_threshold=4.5,
        )
        self.assertIsNone(point.current_value)

        now = datetime.now(timezone.utc)
        point.record_sample(2.35, sampled_at=now)
        self.assertEqual(point.current_value, 2.35)
        self.assertEqual(point.last_sampled_at, now)


if __name__ == "__main__":
    unittest.main()
