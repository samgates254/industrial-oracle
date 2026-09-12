"""Canonical demand representation with information-preserving aggregation."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence, Tuple
from industrial_oracle.domain.demand import DemandOrder
from .identifiers import normalize_identifier


@dataclass(frozen=True)
class NormalizedDemandOrder:
    """Canonical discrete period demand order."""

    resource_id: str
    period: int
    quantity: float


@dataclass(frozen=True)
class NormalizedDemand:
    """Canonical demand collection with read-only aggregated requirement mapping."""

    orders: Tuple[NormalizedDemandOrder, ...]
    demand_by_resource_period: Mapping[Tuple[str, int], float]


def normalize_demand(demand_orders: Sequence[DemandOrder]) -> NormalizedDemand:
    """Normalize demand orders and perform information-preserving aggregation for duplicate (r, t)."""
    demand_map = {}

    for order in demand_orders:
        r_id = normalize_identifier(order.resource_id)
        period = int(order.period)
        qty = float(order.quantity)
        key = (r_id, period)
        demand_map[key] = demand_map.get(key, 0.0) + qty

    sorted_orders = tuple(
        NormalizedDemandOrder(resource_id=k[0], period=k[1], quantity=v)
        for k, v in sorted(demand_map.items(), key=lambda item: (item[0][0], item[0][1]))
    )

    return NormalizedDemand(
        orders=sorted_orders,
        demand_by_resource_period=MappingProxyType(demand_map),
    )
