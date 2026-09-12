"""Inventory holding cost compilation on Inv_{r,t}."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_holding_costs(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile holding cost h_r on Inv_{r,t}."""
    for r in factory.resources:
        r_id = r.resource_id
        h_r = factory.economics.holding_costs.get(r_id, 0.0)
        for t in factory.time_horizon.periods:
            j = registry.get_index("Inv", (r_id, t))
            c[j] += h_r
            if h_r != 0.0:
                provenance.setdefault(j, []).append(
                    CoefficientProvenance(
                        column_index=j,
                        symbol="Inv",
                        indices=(r_id, t),
                        component="HOLDING",
                        rate=h_r,
                        intensity=1.0,
                        duration=1.0,
                        formula=f"{h_r} KSh/(kg*period) * Inv",
                        unit="KSh/(kg*period)",
                    )
                )
