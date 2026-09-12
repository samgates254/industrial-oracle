"""Demand charge compilation on peak apparent power (PeakKVA)."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_demand_charge(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile demand charge rate lambda_D on PeakKVA."""
    j_peak = registry.get_index("PeakKVA", ())
    lambda_D = factory.economics.demand_charge_rate
    c[j_peak] += lambda_D
    if lambda_D != 0.0:
        provenance.setdefault(j_peak, []).append(
            CoefficientProvenance(
                column_index=j_peak,
                symbol="PeakKVA",
                indices=(),
                component="DEMAND_CHARGE",
                rate=lambda_D,
                intensity=1.0,
                duration=1.0,
                formula=f"{lambda_D} KSh/kVA * PeakKVA",
                unit="KSh/kVA",
            )
        )
