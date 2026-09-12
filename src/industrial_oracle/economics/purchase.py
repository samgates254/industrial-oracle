"""Resource procurement cost compilation on Receipts_{r,t}."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_purchase_costs(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile static unit purchase costs q_r on Receipts_{r,t}."""
    for r in factory.resources:
        if r.is_purchasable:
            r_id = r.resource_id
            q_r = factory.economics.purchase_costs.get(r_id, 0.0)
            for t in factory.time_horizon.periods:
                j = registry.get_index("Receipts", (r_id, t))
                c[j] += q_r
                if q_r != 0.0:
                    provenance.setdefault(j, []).append(
                        CoefficientProvenance(
                            column_index=j,
                            symbol="Receipts",
                            indices=(r_id, t),
                            component="PURCHASE",
                            rate=q_r,
                            intensity=1.0,
                            duration=1.0,
                            formula=f"{q_r} KSh/kg * Receipts",
                            unit="KSh/kg",
                        )
                    )
