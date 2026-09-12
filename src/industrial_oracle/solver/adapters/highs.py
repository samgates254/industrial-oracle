"""HiGHS solver adapter consuming sparse CanonicalModel rows via scipy.optimize.milp."""

import time
from typing import List
import numpy as np
import scipy.sparse as sp
from scipy.optimize import Bounds, LinearConstraint, milp

from industrial_oracle.model.compiler import CanonicalModel
from ..errors import SolverExecutionError
from ..interface import SolverInterface
from ..result import SolverResult
from ..status import SolverStatus


class HiGHSSolver(SolverInterface):
    """HiGHS solver backend using scipy.optimize.milp with native sparse constraint assembly."""

    def __init__(self, time_limit: float = 300.0, mip_rel_gap: float = 1e-6):
        self.time_limit = float(time_limit)
        self.mip_rel_gap = float(mip_rel_gap)

    def solve(self, model: CanonicalModel) -> SolverResult:
        """Map CanonicalModel into HiGHS backend and solve."""
        start_time = time.perf_counter()

        N = model.num_variables
        c = np.array(model.c, dtype=float)

        # 1. Integrality vector
        integrality = np.zeros(N, dtype=int)
        for j in model.integer_indices:
            integrality[j] = 1

        # 2. Sparse constraint matrix construction (Zero dense conversion)
        data: List[float] = []
        row_ind: List[int] = []
        col_ind: List[int] = []
        lhs_list: List[float] = []
        rhs_list: List[float] = []

        # Equality rows (lhs == rhs == b_eq)
        for r_idx, row in enumerate(model.A_eq_sparse):
            for col, val in row.coefficients.items():
                data.append(val)
                row_ind.append(r_idx)
                col_ind.append(col)
            lhs_list.append(row.rhs)
            rhs_list.append(row.rhs)

        # Inequality rows (lhs == -inf, rhs == b_ub)
        offset = model.num_equalities
        for u_idx, row in enumerate(model.A_ub_sparse):
            r_idx = offset + u_idx
            for col, val in row.coefficients.items():
                data.append(val)
                row_ind.append(r_idx)
                col_ind.append(col)
            lhs_list.append(-np.inf)
            rhs_list.append(row.rhs)

        M_total = model.num_equalities + model.num_inequalities
        if M_total > 0:
            A_sparse = sp.csc_matrix((data, (row_ind, col_ind)), shape=(M_total, N))
            constraints = LinearConstraint(A_sparse, np.array(lhs_list), np.array(rhs_list))
        else:
            constraints = LinearConstraint(sp.csc_matrix((0, N)), np.array([]), np.array([]))

        # 3. Variable bounds
        bounds = Bounds(np.array(model.l), np.array(model.u))

        # 4. Backend options
        options = {
            "time_limit": self.time_limit,
            "mip_rel_gap": self.mip_rel_gap,
        }

        try:
            res = milp(
                c=c,
                integrality=integrality,
                constraints=constraints,
                bounds=bounds,
                options=options,
            )
            # If backend presolve reports infeasibility, re-verify without presolve to rule out presolve false-infeasible
            if res.status == 2 and options.get("presolve", True):
                options_fallback = dict(options)
                options_fallback["presolve"] = False
                res_fallback = milp(
                    c=c,
                    integrality=integrality,
                    constraints=constraints,
                    bounds=bounds,
                    options=options_fallback,
                )
                if res_fallback.status != 2:
                    res = res_fallback
        except Exception as exc:
            raise SolverExecutionError(f"HiGHS backend encountered execution failure: {exc}") from exc

        elapsed = time.perf_counter() - start_time

        # 5. Status normalization
        # SciPy milp statuses:
        # 0: Optimal solution found
        # 1: Iteration or time limit reached
        # 2: Problem is infeasible
        # 3: Problem is unbounded
        # 4: Other / numerical difficulty
        if res.status == 0:
            status = SolverStatus.OPTIMAL
        elif res.status == 1:
            status = SolverStatus.TIME_LIMIT
        elif res.status == 2:
            status = SolverStatus.INFEASIBLE
        elif res.status == 3:
            status = SolverStatus.UNBOUNDED
        else:
            status = SolverStatus.ERROR

        primal_vals = None
        recomputed_obj = None

        if res.x is not None:
            primal_vals = tuple(float(x) for x in res.x)
            # Recompute objective independently: Z* = c^T y* + FixedCharge
            Z_var = float(np.dot(c, res.x))
            recomputed_obj = Z_var + model.fixed_charge

        return SolverResult(
            status=status,
            primal_values=primal_vals,
            objective_value=recomputed_obj,
            solver_name="HiGHS",
            termination_message=str(res.message),
            solve_time_seconds=elapsed,
        )
