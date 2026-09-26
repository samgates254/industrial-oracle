"""Deterministic exponential backoff retry policy for outbox event delivery."""

from datetime import datetime, timedelta, timezone
from typing import Optional


class RetryPolicy:
    """Configurable exponential backoff retry policy for reliable delivery."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_backoff_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff_seconds: float = 60.0,
    ) -> None:
        self.max_attempts = max(1, max_attempts)
        self.base_backoff_seconds = max(0.1, base_backoff_seconds)
        self.backoff_multiplier = max(1.0, backoff_multiplier)
        self.max_backoff_seconds = max(self.base_backoff_seconds, max_backoff_seconds)

    def should_retry(self, attempts: int) -> bool:
        """Determines if the event can be retried based on attempt count."""
        return attempts < self.max_attempts

    def calculate_delay(self, attempts: int) -> float:
        """Calculates backoff delay in seconds for the given attempt count.

        Attempt 1 -> base_backoff (e.g. 1.0s)
        Attempt 2 -> base_backoff * multiplier (e.g. 2.0s)
        Attempt 3 -> base_backoff * multiplier^2 (e.g. 4.0s)
        """
        exponent = max(0, attempts - 1)
        delay = self.base_backoff_seconds * (self.backoff_multiplier ** exponent)
        return min(delay, self.max_backoff_seconds)

    def calculate_next_available_at(
        self,
        attempts: int,
        current_time: Optional[datetime] = None,
    ) -> datetime:
        """Returns the UTC datetime after which the next retry attempt should occur."""
        now = current_time or datetime.now(timezone.utc)
        delay = self.calculate_delay(attempts)
        return now + timedelta(seconds=delay)
