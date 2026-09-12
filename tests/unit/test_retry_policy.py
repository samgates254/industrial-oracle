"""Unit tests for outbox worker retry policy and backoff calculation."""

from datetime import datetime, timezone
import unittest

from industrial_oracle.integrations.domain.retry_policy import RetryPolicy


class TestRetryPolicy(unittest.TestCase):
    def test_retry_policy_exponential_backoff(self):
        policy = RetryPolicy(max_attempts=4, base_backoff_seconds=1.5, backoff_multiplier=2.0)
        # Attempt 1: 1.5 * 2^0 = 1.5
        self.assertEqual(policy.calculate_delay(1), 1.5)
        # Attempt 2: 1.5 * 2^1 = 3.0
        self.assertEqual(policy.calculate_delay(2), 3.0)
        # Attempt 3: 1.5 * 2^2 = 6.0
        self.assertEqual(policy.calculate_delay(3), 6.0)

    def test_retry_policy_max_backoff_cap(self):
        policy = RetryPolicy(max_attempts=10, base_backoff_seconds=10.0, backoff_multiplier=2.0, max_backoff_seconds=30.0)
        self.assertEqual(policy.calculate_delay(1), 10.0)
        self.assertEqual(policy.calculate_delay(2), 20.0)
        self.assertEqual(policy.calculate_delay(3), 30.0)
        # Higher attempts must stay capped at max_backoff_seconds
        self.assertEqual(policy.calculate_delay(5), 30.0)

    def test_retry_policy_should_retry_boundary(self):
        policy = RetryPolicy(max_attempts=3)
        self.assertTrue(policy.should_retry(0))
        self.assertTrue(policy.should_retry(1))
        self.assertTrue(policy.should_retry(2))
        self.assertFalse(policy.should_retry(3))
        self.assertFalse(policy.should_retry(4))

    def test_retry_policy_next_available_at_calculation(self):
        policy = RetryPolicy(max_attempts=3, base_backoff_seconds=5.0)
        now = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
        next_dt = policy.calculate_next_available_at(attempts=1, current_time=now)
        self.assertEqual((next_dt - now).total_seconds(), 5.0)


if __name__ == "__main__":
    unittest.main()
