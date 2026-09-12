"""Master DiagnosticsEngine orchestrating post-solve inspection."""

from industrial_oracle.model.compiler import CanonicalModel
from industrial_oracle.normalization.factory import NormalizedFactory
from industrial_oracle.solver.result import SolverResult
from industrial_oracle.solver.status import SolverStatus
from .bottlenecks import detect_peak_setting_periods, extract_binding_constraints
from .economics import decompose_economic_costs
from .feasibility import compute_feasibility_metrics
from .flow import compute_resource_flows
from .infeasibility import analyze_infeasibility_evidence
from .operations import compute_machine_operations
from .report import DiagnosticReport


class DiagnosticsEngine:
    """Non-mutating post-solve diagnostics inspection engine."""

    @staticmethod
    def analyze(
        factory: NormalizedFactory,
        model: CanonicalModel,
        result: SolverResult,
    ) -> DiagnosticReport:
        """Generate comprehensive diagnostic report observing factory, model, and result."""
        is_infeasible = result.status == SolverStatus.INFEASIBLE
        primal_vals = result.primal_values if not is_infeasible else None

        # 1. Feasibility Diagnostics
        feasibility_metrics = compute_feasibility_metrics(model, primal_vals)

        # 2. Binding Constraints & Peak Periods
        binding_constraints = extract_binding_constraints(model, primal_vals)
        peak_periods = detect_peak_setting_periods(factory, model, primal_vals)

        # 3. Economic Deconstruction
        economic_breakdown = decompose_economic_costs(factory, model, primal_vals, result.objective_value)

        # 4. Machine Operations
        machine_ops = compute_machine_operations(factory, model, primal_vals)

        # 5. Resource Flow Accounting
        resource_flows = compute_resource_flows(factory, model, primal_vals)

        # 6. Infeasibility Physical Evidence
        infeasibility_evidence = analyze_infeasibility_evidence(factory, is_infeasible)

        return DiagnosticReport(
            factory_name=factory.contract_title,
            solver_status=result.status.value,
            solve_time_seconds=result.solve_time_seconds,
            feasibility=feasibility_metrics,
            binding_constraints=binding_constraints,
            peak_setting_periods=peak_periods,
            economics=economic_breakdown,
            operations=machine_ops,
            resource_flows=resource_flows,
            infeasibility=infeasibility_evidence,
        )
