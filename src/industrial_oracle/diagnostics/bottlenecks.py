"""Bottleneck and binding constraint diagnostics."""

from types import MappingProxyType
from typing import List, Optional, Sequence, Tuple
from industrial_oracle.model.compiler import CanonicalModel
from industrial_oracle.normalization.factory import NormalizedFactory
from .report import BindingConstraintRecord, DIAGNOSTIC_EPSILON


def categorize_equation(eq_id: str) -> str:
    """Determine industrial category from equation ID provenance."""
    if "EQ-CAP" in eq_id:
        return "CAPACITY"
    elif "EQ-MIN" in eq_id:
        return "MIN_LOAD"
    elif "EQ-GRD" in eq_id:
        return "GRID"
    elif "EQ-STRG" in eq_id:
        return "STORAGE"
    elif "EQ-DMD" in eq_id:
        return "DEMAND"
    elif "EQ-STR" in eq_id:
        return "STARTUP"
    elif "EQ-PEAK" in eq_id:
        return "PEAK"
    elif "EQ-BAL" in eq_id:
        return "BALANCE"
    return "OTHER"


def extract_binding_constraints(
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
) -> Tuple[BindingConstraintRecord, ...]:
    """Extract binding inequalities (slack <= epsilon) and satisfied equalities (|res| <= epsilon)."""
    if primal_values is None:
        return ()

    y = primal_values
    records: List[BindingConstraintRecord] = []

    # 1. Equality rows (inherently active / satisfied)
    for idx, row in enumerate(model.A_eq_sparse):
        lhs = sum(val * y[col] for col, val in row.coefficients.items())
        res = lhs - row.rhs
        state = "SATISFIED_EQUALITY" if abs(res) <= DIAGNOSTIC_EPSILON else "VIOLATED_EQUALITY"
        records.append(
            BindingConstraintRecord(
                equation_id=row.equation_id,
                category=categorize_equation(row.equation_id),
                row_index=idx,
                state=state,
                slack=float(abs(res)),
                lhs_value=float(lhs),
                rhs_value=float(row.rhs),
                description=row.description,
            )
        )

    # 2. Inequality rows (Aub y <= bub): slack s = b - Aub y. Binding if s <= epsilon.
    for idx, row in enumerate(model.A_ub_sparse):
        lhs = sum(val * y[col] for col, val in row.coefficients.items())
        slack = row.rhs - lhs
        if slack < -DIAGNOSTIC_EPSILON:
            state = "VIOLATED"
        elif slack <= DIAGNOSTIC_EPSILON:
            state = "BINDING"
        else:
            state = "SLACK"

        if state in ("BINDING", "VIOLATED"):
            records.append(
                BindingConstraintRecord(
                    equation_id=row.equation_id,
                    category=categorize_equation(row.equation_id),
                    row_index=idx,
                    state=state,
                    slack=float(slack),
                    lhs_value=float(lhs),
                    rhs_value=float(row.rhs),
                    description=row.description,
                )
            )

    return tuple(records)


def detect_peak_setting_periods(
    factory: NormalizedFactory,
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
) -> Tuple[int, ...]:
    """Identify periods where period apparent power matches reported PeakKVA."""
    if primal_values is None:
        return ()

    y = primal_values
    reg = model.variable_registry
    peak_kva_sol = y[reg.get_index("PeakKVA", ())]
    delta_t = factory.time_horizon.delta_t
    cos_phi = factory.electrical.power_factor
    periods = factory.time_horizon.periods

    peak_periods: List[int] = []
    for t in periods:
        var_kw = sum(
            m.variable_energy_kwh_per_kg[p] * y[reg.get_index("x", (m.machine_id, p, t))]
            for m in factory.machines for p in m.compatible_processes
        ) / delta_t

        fixed_kw = sum(
            m.fixed_power_kw * y[reg.get_index("z", (m.machine_id, t))]
            for m in factory.machines
        )

        kva_t = (var_kw + fixed_kw) / cos_phi
        if abs(kva_t - peak_kva_sol) <= DIAGNOSTIC_EPSILON:
            peak_periods.append(t)

    return tuple(peak_periods)
