"""Normalized solver status enumeration for V0.1."""

from enum import Enum


class SolverStatus(str, Enum):
    """Normalized, backend-independent solver termination statuses."""

    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNBOUNDED = "UNBOUNDED"
    TIME_LIMIT = "TIME_LIMIT"
    ERROR = "ERROR"
