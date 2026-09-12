"""Infeasibility diagnostics providing evidence without artificial IIS claims."""

from typing import List
from industrial_oracle.normalization.factory import NormalizedFactory
from .report import InfeasibilityEvidence


def analyze_infeasibility_evidence(
    factory: NormalizedFactory,
    is_infeasible: bool,
) -> InfeasibilityEvidence:
    """Identify constraint-level physical evidence for infeasible models."""
    if not is_infeasible:
        return InfeasibilityEvidence(
            is_infeasible=False,
            evidence_messages=(),
            capacity_deficit=0.0,
        )

    messages: List[str] = []
    delta_t = factory.time_horizon.delta_t
    N_T = factory.time_horizon.num_periods

    # 1. Capacity vs Demand Evidence
    total_demand = sum(order.quantity for order in factory.demand.orders)
    total_machine_capacity = sum(m.capacity_rate_kg_per_h * delta_t * N_T for m in factory.machines)

    capacity_deficit = max(0.0, total_demand - total_machine_capacity)
    if capacity_deficit > 0.0:
        messages.append(
            f"CAPACITY_EVIDENCE: Finished-demand volume ({total_demand} kg) exceeds total "
            f"available machine capacity ({total_machine_capacity} kg) by {capacity_deficit} kg."
        )

    # 2. Unreplenishable Safety-Stock Conflict Evidence
    for r in factory.resources:
        if r.initial_stock < r.safety_stock:
            can_purchase = r.is_purchasable
            can_produce = any(p.output_coefficients.get(r.resource_id, 0.0) > 0.0 for p in factory.processes)
            if not can_purchase and not can_produce:
                messages.append(
                    f"UNREPLENISHABLE_SAFETY_STOCK_CONFLICT: Resource '{r.resource_id}' initial stock "
                    f"({r.initial_stock} kg) is below required safety stock ({r.safety_stock} kg), "
                    f"and resource cannot be purchased or produced."
                )

    return InfeasibilityEvidence(
        is_infeasible=True,
        evidence_messages=tuple(messages),
        capacity_deficit=float(capacity_deficit),
    )
