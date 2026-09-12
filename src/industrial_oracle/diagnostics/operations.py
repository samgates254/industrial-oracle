"""Machine operational metrics: utilization, operating hours, and startup counts."""

from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.compiler import CanonicalModel
from .report import DIAGNOSTIC_EPSILON, MachineOperationMetrics


def compute_machine_operations(
    factory: NormalizedFactory,
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
) -> Mapping[str, MachineOperationMetrics]:
    """Calculate period utilization, mean utilization, operating hours, and startups for all machines."""
    if primal_values is None:
        return MappingProxyType({})

    y = primal_values
    reg = model.variable_registry
    delta_t = factory.time_horizon.delta_t
    periods = factory.time_horizon.periods
    N_T = factory.time_horizon.num_periods

    metrics_map: Dict[str, MachineOperationMetrics] = {}

    for m in factory.machines:
        m_id = m.machine_id
        cap_period = m.capacity_rate_kg_per_h * delta_t
        period_util: Dict[int, float] = {}
        operating_hours = 0.0
        total_startups = 0

        for t in periods:
            q_mt = sum(
                y[reg.get_index("x", (m_id, p, t))]
                for p in m.compatible_processes
            )
            u_mt = (q_mt / cap_period) if cap_period > 0.0 else 0.0
            period_util[t] = float(u_mt)

            if q_mt > DIAGNOSTIC_EPSILON:
                operating_hours += delta_t

            s_mt = y[reg.get_index("Startup", (m_id, t))]
            if round(s_mt) == 1:
                total_startups += 1

        avg_util = sum(period_util.values()) / float(N_T) if N_T > 0 else 0.0

        metrics_map[m_id] = MachineOperationMetrics(
            machine_id=m_id,
            period_utilization=MappingProxyType(period_util),
            average_utilization=float(avg_util),
            operating_hours=float(operating_hours),
            total_startups=int(total_startups),
        )

    return MappingProxyType(metrics_map)
