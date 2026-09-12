"""Immutable solver result representation."""

from dataclasses import dataclass
from typing import Any, Optional, Tuple
from industrial_oracle.model.variables import VariableRegistry
from .status import SolverStatus


@dataclass(frozen=True)
class SolverResult:
    """Authoritative immutable result from solving a CanonicalModel."""

    status: SolverStatus
    primal_values: Optional[Tuple[float, ...]] = None
    objective_value: Optional[float] = None
    solver_name: str = ""
    termination_message: str = ""
    solve_time_seconds: float = 0.0

    @property
    def is_optimal(self) -> bool:
        return self.status == SolverStatus.OPTIMAL

    @property
    def is_feasible(self) -> bool:
        return self.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)

    def get_value(self, symbol: str, indices: Tuple[Any, ...], registry: VariableRegistry) -> Optional[float]:
        """Extract the solution value of a variable via symbolic index lookup."""
        if self.primal_values is None:
            return None
        col = registry.get_index(symbol, indices)
        return self.primal_values[col]
