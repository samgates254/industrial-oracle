"""Canonical machine representation."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple
from industrial_oracle.domain.machines import Machine
from .identifiers import normalize_identifier


@dataclass(frozen=True)
class NormalizedMachine:
    """Canonical machine asset representation with read-only mappings."""

    machine_id: str
    capacity_rate_kg_per_h: float
    min_load_rate_kg_per_h: float
    fixed_power_kw: float
    initial_state: int
    compatible_processes: Tuple[str, ...]
    variable_energy_kwh_per_kg: Mapping[str, float]


def normalize_machine(mach: Machine) -> NormalizedMachine:
    """Normalize Machine entity with deterministic sorted collections and read-only mappings."""
    canonical_id = normalize_identifier(mach.machine_id)
    canonical_compat = tuple(sorted(normalize_identifier(p) for p in mach.compatible_processes))
    canonical_energy = {
        normalize_identifier(p): float(e)
        for p, e in sorted(mach.variable_energy.items(), key=lambda item: normalize_identifier(item[0]))
    }

    return NormalizedMachine(
        machine_id=canonical_id,
        capacity_rate_kg_per_h=float(mach.capacity_rate),
        min_load_rate_kg_per_h=float(mach.min_load_rate),
        fixed_power_kw=float(mach.fixed_power),
        initial_state=int(mach.initial_state),
        compatible_processes=canonical_compat,
        variable_energy_kwh_per_kg=MappingProxyType(canonical_energy),
    )
