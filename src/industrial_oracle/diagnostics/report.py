"""Immutable diagnostic data structures and canonical tolerance."""

from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

DIAGNOSTIC_EPSILON: float = 1e-6


@dataclass(frozen=True)
class FeasibilityMetrics:
    """Numerical validation metrics for a primal solution candidate."""

    max_equality_residual: float
    max_inequality_violation: float
    max_bound_violation: float
    max_integrality_residual: float
    max_violation: float
    is_verified_feasible: bool


@dataclass(frozen=True)
class BindingConstraintRecord:
    """Record for a binding or active constraint."""

    equation_id: str
    category: str
    row_index: int
    state: str
    slack: float
    lhs_value: float
    rhs_value: float
    description: str


@dataclass(frozen=True)
class CostComponentBreakdown:
    """Seven-component economic valuation breakdown and percentage shares."""

    energy_variable: float
    energy_fixed: float
    demand_charge: float
    purchase: float
    startup: float
    holding: float
    shortfall: float
    fixed_charge: float
    total_cost: float
    reconstruction_residual: float
    percentage_shares: Mapping[str, float]


@dataclass(frozen=True)
class MachineOperationMetrics:
    """Operational utilization and activity metrics for a machine."""

    machine_id: str
    period_utilization: Mapping[int, float]
    average_utilization: float
    operating_hours: float
    total_startups: int


@dataclass(frozen=True)
class ResourceFlowRecord:
    """Independent mass flow accounting and conservation verification for a resource."""

    resource_id: str
    initial_stock: float
    total_receipts: float
    total_produced: float
    total_consumed: float
    total_shipped: float
    final_stock: float
    conservation_residual: float


@dataclass(frozen=True)
class InfeasibilityEvidence:
    """Physical and structural evidence of infeasibility."""

    is_infeasible: bool
    evidence_messages: Tuple[str, ...]
    capacity_deficit: float


@dataclass(frozen=True)
class DiagnosticReport:
    """Authoritative immutable post-solve inspection report."""

    factory_name: str
    solver_status: str
    solve_time_seconds: float
    feasibility: FeasibilityMetrics
    binding_constraints: Tuple[BindingConstraintRecord, ...]
    peak_setting_periods: Tuple[int, ...]
    economics: CostComponentBreakdown
    operations: Mapping[str, MachineOperationMetrics]
    resource_flows: Mapping[str, ResourceFlowRecord]
    infeasibility: InfeasibilityEvidence
