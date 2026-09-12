"""Machine startup cost compilation on Startup_{m,t}."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_startup_costs(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile setup/startup cost s_m on Startup_{m,t}."""
    for m in factory.machines:
        m_id = m.machine_id
        s_m = factory.economics.setup_costs.get(m_id, 0.0)
        for t in factory.time_horizon.periods:
            j = registry.get_index("Startup", (m_id, t))
            c[j] += s_m
            if s_m != 0.0:
                provenance.setdefault(j, []).append(
                    CoefficientProvenance(
                        column_index=j,
                        symbol="Startup",
                        indices=(m_id, t),
                        component="STARTUP",
                        rate=s_m,
                        intensity=1.0,
                        duration=1.0,
                        formula=f"{s_m} KSh/startup * Startup",
                        unit="KSh/startup",
                    )
                )
