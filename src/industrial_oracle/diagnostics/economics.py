"""Economic cost decomposition into the seven constituent components."""

from types import MappingProxyType
from typing import Dict, Optional, Sequence
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.model.compiler import CanonicalModel
from .report import CostComponentBreakdown, DIAGNOSTIC_EPSILON


def decompose_economic_costs(
    factory: NormalizedFactory,
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
    reported_objective: Optional[float],
) -> CostComponentBreakdown:
    """Decompose total operating cost Z into its 7 exact terms and compute percentage shares."""
    if primal_values is None:
        return CostComponentBreakdown(
            energy_variable=0.0,
            energy_fixed=0.0,
            demand_charge=0.0,
            purchase=0.0,
            startup=0.0,
            holding=0.0,
            shortfall=0.0,
            fixed_charge=float(factory.economics.fixed_charge),
            total_cost=float(factory.economics.fixed_charge),
            reconstruction_residual=0.0,
            percentage_shares=MappingProxyType({}),
        )

    y = primal_values
    reg = model.variable_registry
    tariffs = factory.tariff_schedule.energy_rates
    delta_t = factory.time_horizon.delta_t
    econ = factory.economics
    periods = factory.time_horizon.periods

    # 1. Variable energy
    z_energy_var = sum(
        tariffs[t] * m.variable_energy_kwh_per_kg[p] * y[reg.get_index("x", (m.machine_id, p, t))]
        for m in factory.machines for p in m.compatible_processes for t in periods
    )

    # 2. Fixed energy
    z_energy_fixed = sum(
        tariffs[t] * m.fixed_power_kw * delta_t * y[reg.get_index("z", (m.machine_id, t))]
        for m in factory.machines for t in periods
    )

    # 3. Demand charge
    z_demand = econ.demand_charge_rate * y[reg.get_index("PeakKVA", ())]

    # 4. Purchase costs
    z_purchase = sum(
        econ.purchase_costs.get(r.resource_id, 0.0) * y[reg.get_index("Receipts", (r.resource_id, t))]
        for r in factory.resources if r.is_purchasable for t in periods
    )

    # 5. Startup costs
    z_startup = sum(
        econ.setup_costs.get(m.machine_id, 0.0) * y[reg.get_index("Startup", (m.machine_id, t))]
        for m in factory.machines for t in periods
    )

    # 6. Holding costs
    z_holding = sum(
        econ.holding_costs.get(r.resource_id, 0.0) * y[reg.get_index("Inv", (r.resource_id, t))]
        for r in factory.resources for t in periods
    )

    # 7. Shortfall penalty
    if factory.configuration_policy.allow_demand_shortfall:
        z_shortfall = sum(
            econ.penalty_costs.get(r.resource_id, 0.0) * y[reg.get_index("Short", (r.resource_id, t))]
            for r in factory.resources if r.category == "FINISHED" for t in periods
        )
    else:
        z_shortfall = 0.0

    # Fixed facility charge
    f_charge = float(econ.fixed_charge)

    # Total reconstructed cost
    z_reconstructed = (
        z_energy_var + z_energy_fixed + z_demand +
        z_purchase + z_startup + z_holding + z_shortfall + f_charge
    )

    residual = abs(z_reconstructed - reported_objective) if reported_objective is not None else 0.0

    # Compute percentage shares (avoid division by zero if Z <= epsilon)
    shares: Dict[str, float] = {}
    if abs(z_reconstructed) > DIAGNOSTIC_EPSILON:
        shares = {
            "energy_variable": (z_energy_var / z_reconstructed) * 100.0,
            "energy_fixed": (z_energy_fixed / z_reconstructed) * 100.0,
            "demand_charge": (z_demand / z_reconstructed) * 100.0,
            "purchase": (z_purchase / z_reconstructed) * 100.0,
            "startup": (z_startup / z_reconstructed) * 100.0,
            "holding": (z_holding / z_reconstructed) * 100.0,
            "shortfall": (z_shortfall / z_reconstructed) * 100.0,
            "fixed_charge": (f_charge / z_reconstructed) * 100.0,
        }
    else:
        shares = {
            "energy_variable": 0.0, "energy_fixed": 0.0, "demand_charge": 0.0,
            "purchase": 0.0, "startup": 0.0, "holding": 0.0,
            "shortfall": 0.0, "fixed_charge": 0.0,
        }

    return CostComponentBreakdown(
        energy_variable=float(z_energy_var),
        energy_fixed=float(z_energy_fixed),
        demand_charge=float(z_demand),
        purchase=float(z_purchase),
        startup=float(z_startup),
        holding=float(z_holding),
        shortfall=float(z_shortfall),
        fixed_charge=f_charge,
        total_cost=float(z_reconstructed),
        reconstruction_residual=float(residual),
        percentage_shares=MappingProxyType(shares),
    )
