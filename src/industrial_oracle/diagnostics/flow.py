"""Resource flow accounting and mass conservation verification."""

from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.compiler import CanonicalModel
from .report import ResourceFlowRecord


def compute_resource_flows(
    factory: NormalizedFactory,
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
) -> Mapping[str, ResourceFlowRecord]:
    """Independently reconstruct material accounting (Inflow == Outflow) across horizon."""
    if primal_values is None:
        return MappingProxyType({})

    y = primal_values
    reg = model.variable_registry
    periods = factory.time_horizon.periods
    N_T = factory.time_horizon.num_periods

    flow_map: Dict[str, ResourceFlowRecord] = {}

    for r in factory.resources:
        r_id = r.resource_id

        # 1. Total Produced across horizon: sum_{t,m,p} b_{r,p} * x_{m,p,t}
        total_produced = sum(
            p.output_coefficients.get(r_id, 0.0) * y[reg.get_index("x", (m_id, p.process_id, t))]
            for p in factory.processes for m_id in factory.indexes.M_p[p.process_id] for t in periods
        )

        # 2. Total Consumed across horizon: sum_{t,m,p} a_{r,p} * x_{m,p,t}
        total_consumed = sum(
            p.input_coefficients.get(r_id, 0.0) * y[reg.get_index("x", (m_id, p.process_id, t))]
            for p in factory.processes for m_id in factory.indexes.M_p[p.process_id] for t in periods
        )

        # 3. Total Receipts
        total_receipts = sum(
            y[reg.get_index("Receipts", (r_id, t))]
            for t in periods
        ) if r.is_purchasable else 0.0

        # 4. Total Shipped
        total_shipped = sum(
            y[reg.get_index("Ship", (r_id, t))]
            for t in periods
        ) if r.category == "FINISHED" else 0.0

        # 5. Final Stock at t=N_T
        final_stock = y[reg.get_index("Inv", (r_id, N_T))]

        # 6. Conservation Residual: Initial + Receipts + Produced - Consumed - Shipped - FinalStock
        conservation_residual = (
            r.initial_stock + total_receipts + total_produced -
            total_consumed - total_shipped - final_stock
        )

        flow_map[r_id] = ResourceFlowRecord(
            resource_id=r_id,
            initial_stock=float(r.initial_stock),
            total_receipts=float(total_receipts),
            total_produced=float(total_produced),
            total_consumed=float(total_consumed),
            total_shipped=float(total_shipped),
            final_stock=float(final_stock),
            conservation_residual=float(conservation_residual),
        )

    return MappingProxyType(flow_map)
