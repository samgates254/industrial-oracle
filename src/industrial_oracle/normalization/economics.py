"""Canonical economic parameters."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from industrial_oracle.domain.economics import Economics
from .identifiers import normalize_identifier


@dataclass(frozen=True)
class NormalizedEconomics:
    """Canonical economic rates and read-only cost mappings."""

    c_peak: float
    c_offpeak: float
    c_shoulder: float
    demand_charge_rate: float
    fixed_charge: float
    purchase_costs: Mapping[str, float]
    setup_costs: Mapping[str, float]
    holding_costs: Mapping[str, float]
    penalty_costs: Mapping[str, float]


def normalize_economics(econ: Economics) -> NormalizedEconomics:
    """Normalize Economics domain object with sorted keys and read-only mappings."""
    return NormalizedEconomics(
        c_peak=float(econ.energy_tariffs.c_peak),
        c_offpeak=float(econ.energy_tariffs.c_offpeak),
        c_shoulder=float(econ.energy_tariffs.c_shoulder),
        demand_charge_rate=float(econ.demand_charge_rate),
        fixed_charge=float(econ.fixed_charge),
        purchase_costs=MappingProxyType({
            normalize_identifier(k): float(v)
            for k, v in sorted(econ.purchase_costs.items(), key=lambda item: normalize_identifier(item[0]))
        }),
        setup_costs=MappingProxyType({
            normalize_identifier(k): float(v)
            for k, v in sorted(econ.setup_costs.items(), key=lambda item: normalize_identifier(item[0]))
        }),
        holding_costs=MappingProxyType({
            normalize_identifier(k): float(v)
            for k, v in sorted(econ.holding_costs.items(), key=lambda item: normalize_identifier(item[0]))
        }),
        penalty_costs=MappingProxyType({
            normalize_identifier(k): float(v)
            for k, v in sorted(econ.penalty_costs.items(), key=lambda item: normalize_identifier(item[0]))
        }),
    )
