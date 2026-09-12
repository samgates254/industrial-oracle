"""Abstract SolverInterface protocol."""

from abc import ABC, abstractmethod
from industrial_oracle.model.compiler import CanonicalModel
from .result import SolverResult


class SolverInterface(ABC):
    """Abstract base class for replaceable optimization solver backends."""

    @abstractmethod
    def solve(self, model: CanonicalModel) -> SolverResult:
        """Solve the canonical mathematical model and return a normalized SolverResult."""
        pass
