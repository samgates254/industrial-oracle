"""Canonical electrical parameters."""

from dataclasses import dataclass
from industrial_oracle.domain.electrical import ElectricalParameters


@dataclass(frozen=True)
class NormalizedElectricalParameters:
    """Canonical electrical grid and power parameters."""

    power_factor: float
    contract_limit_kva: float


def normalize_electrical(elec: ElectricalParameters) -> NormalizedElectricalParameters:
    """Normalize ElectricalParameters domain object."""
    return NormalizedElectricalParameters(
        power_factor=float(elec.power_factor),
        contract_limit_kva=float(elec.contract_limit_kva),
    )
