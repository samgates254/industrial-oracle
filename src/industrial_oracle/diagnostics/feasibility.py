"""Feasibility diagnostics evaluating equality, inequality, bounds, and integrality residuals."""

from typing import Optional, Sequence
from industrial_oracle.model.compiler import CanonicalModel
from .report import DIAGNOSTIC_EPSILON, FeasibilityMetrics


def compute_feasibility_metrics(
    model: CanonicalModel,
    primal_values: Optional[Sequence[float]],
) -> FeasibilityMetrics:
    """Compute maximum residuals across all canonical equations and bounds."""
    if primal_values is None:
        return FeasibilityMetrics(
            max_equality_residual=0.0,
            max_inequality_violation=0.0,
            max_bound_violation=0.0,
            max_integrality_residual=0.0,
            max_violation=0.0,
            is_verified_feasible=False,
        )

    y = primal_values

    # 1. Equality residual: R_{eq,max} = max_i |A_{eq} y - b_{eq,i}|
    if len(model.A_eq_sparse) > 0:
        max_eq = max(
            abs(sum(val * y[col] for col, val in row.coefficients.items()) - row.rhs)
            for row in model.A_eq_sparse
        )
    else:
        max_eq = 0.0

    # 2. Inequality violation: V_{ub,max} = max(0, max_i (A_{ub} y - b_{ub,i}))
    if len(model.A_ub_sparse) > 0:
        max_ub_viol = max(
            0.0,
            max(
                sum(val * y[col] for col, val in row.coefficients.items()) - row.rhs
                for row in model.A_ub_sparse
            ),
        )
    else:
        max_ub_viol = 0.0

    # 3. Bound violation: V_{bound,max} = max(0, max_j(l_j - y_j), max_j(y_j - u_j))
    viol_lower = max(0.0, max((model.l[j] - y[j] for j in range(model.num_variables)), default=0.0))
    viol_upper = max(0.0, max((y[j] - model.u[j] for j in range(model.num_variables)), default=0.0))
    max_bound_viol = max(viol_lower, viol_upper)

    # 4. Integrality residual: R_{int,max} = max_{j in I} |y_j - round(y_j)|
    if len(model.integer_indices) > 0:
        max_int = max(abs(y[j] - round(y[j])) for j in model.integer_indices)
    else:
        max_int = 0.0

    # 5. Maximum system violation
    max_violation = max(max_eq, max_ub_viol, max_bound_viol, max_int)
    is_feasible = max_violation <= DIAGNOSTIC_EPSILON

    return FeasibilityMetrics(
        max_equality_residual=float(max_eq),
        max_inequality_violation=float(max_ub_viol),
        max_bound_violation=float(max_bound_viol),
        max_integrality_residual=float(max_int),
        max_violation=float(max_violation),
        is_verified_feasible=is_feasible,
    )
