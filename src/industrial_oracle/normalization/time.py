"""Canonical time normalization."""

from dataclasses import dataclass
from typing import Tuple
from industrial_oracle.domain.time import TimeHorizon


@dataclass(frozen=True)
class NormalizedTimeHorizon:
    """Canonical discrete-time horizon representation."""

    num_periods: int
    delta_t: float
    periods: Tuple[int, ...]


def normalize_time_horizon(th: TimeHorizon) -> NormalizedTimeHorizon:
    """Convert TimeHorizon domain object to canonical representation."""
    canonical_periods = tuple(range(1, th.num_periods + 1))
    return NormalizedTimeHorizon(
        num_periods=int(th.num_periods),
        delta_t=float(th.delta_t),
        periods=canonical_periods,
    )
