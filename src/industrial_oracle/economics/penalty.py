"""Demand shortfall penalty compilation on Short_{r,t}."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_penalty_costs(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile shortfall penalty p_r on Short_{r,t} in soft-demand mode."""
    if not factory.configuration_policy.allow_demand_shortfall:
        return

    for r in factory.resources:
        if r.category == "FINISHED":
            r_id = r.resource_id
            p_r = factory.economics.penalty_costs.get(r_id, 0.0)
            for t in factory.time_horizon.periods:
                j = registry.get_index("Short", (r_id, t))
                c[j] += p_r
                if p_r != 0.0:
                    provenance.setdefault(j, []).append(
                        CoefficientProvenance(
                            column_index=j,
                            symbol="Short",
                            indices=(r_id, t),
                            component="SHORTFALL",
                            rate=p_r,
                            intensity=1.0,
                            duration=1.0,
                            formula=f"{p_r} KSh/kg * Short",
                            unit="KSh/kg",
                        )
                    )
