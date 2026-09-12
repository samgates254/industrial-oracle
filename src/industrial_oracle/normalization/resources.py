"""Canonical resource representation."""

import math
from dataclasses import dataclass
from typing import Tuple
from industrial_oracle.domain.resources import Resource
from .identifiers import normalize_identifier


@dataclass(frozen=True)
class NormalizedResource:
    """Canonical resource record with explicit supply cap values."""

    resource_id: str
    category: str
    initial_stock: float
    safety_stock: float
    max_storage: float
    is_purchasable: bool
    supply_cap: Tuple[float, ...]


def normalize_resource(res: Resource, num_periods: int) -> NormalizedResource:
    """Normalize Resource entity into canonical form."""
    canonical_id = normalize_identifier(res.resource_id)

    if res.supply_cap is None:
        canonical_caps = tuple(math.inf for _ in range(num_periods))
    else:
        canonical_caps = tuple(float(c) for c in res.supply_cap)

    return NormalizedResource(
        resource_id=canonical_id,
        category=res.category.value,
        initial_stock=float(res.initial_stock),
        safety_stock=float(res.safety_stock),
        max_storage=float(res.max_storage),
        is_purchasable=bool(res.is_purchasable),
        supply_cap=canonical_caps,
    )
