"""Canonical constraint compiler for LP/MILP representation."""

from typing import Dict, List, Tuple
from industrial_oracle.normalization.factory import NormalizedFactory
from .equations import SparseRow, make_sparse_row
from .variables import VariableRegistry


def compile_constraints(
    factory: NormalizedFactory,
    registry: VariableRegistry,
) -> Tuple[Tuple[SparseRow, ...], Tuple[SparseRow, ...]]:
    """Compile all equality (A_eq, b_eq) and inequality (A_ub, b_ub) constraints."""
    eq_rows: List[SparseRow] = []
    ub_rows: List[SparseRow] = []

    N_T = factory.time_horizon.num_periods
    delta_t = factory.time_horizon.delta_t
    cos_phi = factory.electrical.power_factor
    periods = factory.time_horizon.periods

    R_purchasable = {r.resource_id for r in factory.resources if r.is_purchasable}
    R_finished = {r.resource_id for r in factory.resources if r.category == "FINISHED"}
    demand_map = factory.demand.demand_by_resource_period
    mach_map = {m.machine_id: m for m in factory.machines}

    # =========================================================================
    # EQUALITY CONSTRAINTS (A_eq y = b_eq)
    # =========================================================================

    # 1. Resource Balance: EQ-BAL-001A (t=1) and EQ-BAL-001B (t>=2)
    for r in factory.resources:
        r_id = r.resource_id

        # Period t = 1: Inv_{r,1} - sum_p (b-a) sum_m x_{m,p,1} - Receipts + Ship = InitialStock
        c1: Dict[int, float] = {}
        c1[registry.get_index("Inv", (r_id, 1))] = 1.0

        for p in factory.processes:
            p_id = p.process_id
            b_val = p.output_coefficients.get(r_id, 0.0)
            a_val = p.input_coefficients.get(r_id, 0.0)
            net_coeff = b_val - a_val
            if abs(net_coeff) > 1e-12:
                for m_id in factory.indexes.M_p[p_id]:
                    j_x = registry.get_index("x", (m_id, p_id, 1))
                    c1[j_x] = c1.get(j_x, 0.0) - net_coeff

        if r_id in R_purchasable:
            c1[registry.get_index("Receipts", (r_id, 1))] = -1.0

        if r_id in R_finished:
            c1[registry.get_index("Ship", (r_id, 1))] = 1.0

        eq_rows.append(
            make_sparse_row(
                equation_id=f"EQ-BAL-001A_{r_id}_1",
                raw_coeffs=c1,
                rhs=r.initial_stock,
                description=f"Resource balance for {r_id} at t=1 (anchored to InitialStock)",
            )
        )

        # Period t >= 2: Inv_{r,t} - Inv_{r,t-1} - sum_p (b-a) sum_m x_{m,p,t} - Receipts + Ship = 0
        for t in range(2, N_T + 1):
            ct: Dict[int, float] = {}
            ct[registry.get_index("Inv", (r_id, t))] = 1.0
            ct[registry.get_index("Inv", (r_id, t - 1))] = -1.0

            for p in factory.processes:
                p_id = p.process_id
                b_val = p.output_coefficients.get(r_id, 0.0)
                a_val = p.input_coefficients.get(r_id, 0.0)
                net_coeff = b_val - a_val
                if abs(net_coeff) > 1e-12:
                    for m_id in factory.indexes.M_p[p_id]:
                        j_x = registry.get_index("x", (m_id, p_id, t))
                        ct[j_x] = ct.get(j_x, 0.0) - net_coeff

            if r_id in R_purchasable:
                ct[registry.get_index("Receipts", (r_id, t))] = -1.0

            if r_id in R_finished:
                ct[registry.get_index("Ship", (r_id, t))] = 1.0

            eq_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-BAL-001B_{r_id}_{t}",
                    raw_coeffs=ct,
                    rhs=0.0,
                    description=f"Resource balance for {r_id} at t={t}",
                )
            )

    # 2. Demand Fulfillment: EQ-DMD-001
    for r_id in factory.indexes.R:
        if r_id in R_finished:
            for t in periods:
                cd: Dict[int, float] = {}
                cd[registry.get_index("Ship", (r_id, t))] = 1.0
                if factory.configuration_policy.allow_demand_shortfall:
                    cd[registry.get_index("Short", (r_id, t))] = 1.0

                req_demand = demand_map.get((r_id, t), 0.0)
                eq_rows.append(
                    make_sparse_row(
                        equation_id=f"EQ-DMD-001_{r_id}_{t}",
                        raw_coeffs=cd,
                        rhs=req_demand,
                        description=f"Demand fulfillment for {r_id} at t={t}",
                    )
                )

    # =========================================================================
    # INEQUALITY CONSTRAINTS (A_ub y <= b_ub)
    # =========================================================================

    # 1. Machine Aggregate Capacity: EQ-CAP-001
    for m in factory.machines:
        m_id = m.machine_id
        cap_val = m.capacity_rate_kg_per_h * delta_t
        for t in periods:
            ccap: Dict[int, float] = {}
            for p_id in m.compatible_processes:
                ccap[registry.get_index("x", (m_id, p_id, t))] = 1.0
            ccap[registry.get_index("z", (m_id, t))] = -cap_val

            ub_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-CAP-001_{m_id}_{t}",
                    raw_coeffs=ccap,
                    rhs=0.0,
                    description=f"Machine capacity envelope for {m_id} at t={t}",
                )
            )

    # 2. Machine Aggregate Minimum Load: EQ-MIN-001
    for m in factory.machines:
        m_id = m.machine_id
        min_val = m.min_load_rate_kg_per_h * delta_t
        for t in periods:
            cmin: Dict[int, float] = {}
            for p_id in m.compatible_processes:
                cmin[registry.get_index("x", (m_id, p_id, t))] = -1.0
            cmin[registry.get_index("z", (m_id, t))] = min_val

            ub_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-MIN-001_{m_id}_{t}",
                    raw_coeffs=cmin,
                    rhs=0.0,
                    description=f"Machine minimum load threshold for {m_id} at t={t}",
                )
            )

    # 3. Machine Startup Triad: EQ-STR-001, EQ-STR-002, EQ-STR-003
    for m in factory.machines:
        m_id = m.machine_id
        z0 = float(m.initial_state)

        for t in periods:
            # EQ-STR-001: -Startup_{m,t} + z_{m,t} - z_{m,t-1} <= 0
            cs1: Dict[int, float] = {}
            cs1[registry.get_index("Startup", (m_id, t))] = -1.0
            cs1[registry.get_index("z", (m_id, t))] = 1.0
            if t == 1:
                rhs1 = z0
            else:
                cs1[registry.get_index("z", (m_id, t - 1))] = -1.0
                rhs1 = 0.0

            ub_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-STR-001_{m_id}_{t}",
                    raw_coeffs=cs1,
                    rhs=rhs1,
                    description=f"Startup turn-on lower bound for {m_id} at t={t}",
                )
            )

            # EQ-STR-002: Startup_{m,t} - z_{m,t} <= 0
            cs2: Dict[int, float] = {}
            cs2[registry.get_index("Startup", (m_id, t))] = 1.0
            cs2[registry.get_index("z", (m_id, t))] = -1.0
            ub_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-STR-002_{m_id}_{t}",
                    raw_coeffs=cs2,
                    rhs=0.0,
                    description=f"Startup online bound for {m_id} at t={t}",
                )
            )

            # EQ-STR-003: Startup_{m,t} + z_{m,t-1} <= 1
            cs3: Dict[int, float] = {}
            cs3[registry.get_index("Startup", (m_id, t))] = 1.0
            if t == 1:
                rhs3 = 1.0 - z0
            else:
                cs3[registry.get_index("z", (m_id, t - 1))] = 1.0
                rhs3 = 1.0

            ub_rows.append(
                make_sparse_row(
                    equation_id=f"EQ-STR-003_{m_id}_{t}",
                    raw_coeffs=cs3,
                    rhs=rhs3,
                    description=f"Startup offline transition bound for {m_id} at t={t}",
                )
            )

    # 4. Apparent Power Peak Envelope: EQ-PEAK-001
    j_peak = registry.get_index("PeakKVA", ())
    for t in periods:
        cpk: Dict[int, float] = {}
        for m in factory.machines:
            m_id = m.machine_id
            for p_id in m.compatible_processes:
                e_var = m.variable_energy_kwh_per_kg[p_id]
                coeff_x = e_var / (delta_t * cos_phi)
                j_x = registry.get_index("x", (m_id, p_id, t))
                cpk[j_x] = cpk.get(j_x, 0.0) + coeff_x

            e_fixed = m.fixed_power_kw
            coeff_z = e_fixed / cos_phi
            j_z = registry.get_index("z", (m_id, t))
            cpk[j_z] = cpk.get(j_z, 0.0) + coeff_z

        cpk[j_peak] = -1.0

        ub_rows.append(
            make_sparse_row(
                equation_id=f"EQ-PEAK-001_{t}",
                raw_coeffs=cpk,
                rhs=0.0,
                description=f"Peak kVA envelope lower bound at t={t}",
            )
        )

    return tuple(eq_rows), tuple(ub_rows)
