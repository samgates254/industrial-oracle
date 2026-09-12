"""Solver exceptions hierarchy."""


class SolverError(Exception):
    """Base exception for solver backend failures."""


class SolverBackendNotFoundError(SolverError):
    """Raised when a requested solver backend is not installed or available."""


class SolverExecutionError(SolverError):
    """Raised when a solver backend experiences an internal runtime error."""
