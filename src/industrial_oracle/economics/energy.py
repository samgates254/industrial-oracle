"""Energy cost compilation: variable throughput and fixed online power."""

from typing import Dict, List
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.variables import VariableRegistry
from .traceability import CoefficientProvenance


def compile_energy_coefficients(
    factory: NormalizedFactory,
    registry: VariableRegistry,
    c: List[float],
    provenance: Dict[int, List[CoefficientProvenance]],
) -> None:
    """Compile variable energy (pi_t * e_var) and fixed power (pi_t * e_fixed * delta_t)."""
    delta_t = factory.time_horizon.delta_t
    tariffs = factory.tariff_schedule.energy_rates

    # 1. Variable energy cost on x_{m,p,t}
    for m in factory.machines:
        m_id = m.machine_id
        for p_id in m.compatible_processes:
            e_var = m.variable_energy_kwh_per_kg[p_id]
            for t in factory.time_horizon.periods:
                j = registry.get_index("x", (m_id, p_id, t))
                pi_t = tariffs[t]
                coeff = pi_t * e_var
                c[j] += coeff
                if coeff != 0.0:
                    provenance.setdefault(j, []).append(
                        CoefficientProvenance(
                            column_index=j,
                            symbol="x",
                            indices=(m_id, p_id, t),
                            component="ENERGY_VARIABLE",
                            rate=pi_t,
                            intensity=e_var,
                            duration=1.0,
                            formula=f"{pi_t} KSh/kWh * {e_var} kWh/kg = {coeff} KSh/kg",
                            unit="KSh/kg",
                        )
                    )

    # 2. Fixed energy cost on z_{m,t}
    for m in factory.machines:
        m_id = m.machine_id
        e_fixed = m.fixed_power_kw
        for t in factory.time_horizon.periods:
            j = registry.get_index("z", (m_id, t))
            pi_t = tariffs[t]
            coeff = pi_t * e_fixed * delta_t
            c[j] += coeff
            if coeff != 0.0:
                provenance.setdefault(j, []).append(
                    CoefficientProvenance(
                        column_index=j,
                        symbol="z",
                        indices=(m_id, t),
                        component="ENERGY_FIXED",
                        rate=pi_t,
                        intensity=e_fixed,
                        duration=delta_t,
                        formula=f"{pi_t} KSh/kWh * {e_fixed} kW * {delta_t} h = {coeff} KSh",
                        unit="KSh",
                    )
                )
