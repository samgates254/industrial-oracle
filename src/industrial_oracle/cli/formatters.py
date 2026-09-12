"""Human-readable terminal formatting for diagnostic inspection and CLI summaries."""

from industrial_oracle.diagnostics.report import DiagnosticReport


def format_terminal_summary(report: DiagnosticReport) -> str:
    """Format DiagnosticReport into an auditable, structured terminal view."""
    lines = []
    separator = "=" * 72
    sub_separator = "-" * 72

    lines.append(separator)
    lines.append(f"INDUSTRIAL COST & OPTIMIZATION ORACLE V0.1 — REPORT")
    lines.append(f"System / Contract: {report.factory_name}")
    lines.append(f"Solver Status:     {report.solver_status}")
    lines.append(f"Solve Time:        {report.solve_time_seconds:.4f} seconds")
    lines.append(separator)

    # Infeasibility Alert
    if report.infeasibility.is_infeasible:
        lines.append("STATUS ALERT: MODEL IS INFEASIBLE")
        for msg in report.infeasibility.evidence_messages:
            lines.append(f"  * {msg}")
        lines.append(separator)
        return chr(10).join(lines)

    # Feasibility Section
    feas = report.feasibility
    lines.append("1. PRIMAL FEASIBILITY METRICS")
    lines.append(f"   Verified Feasible:       {'YES' if feas.is_verified_feasible else 'NO'}")
    lines.append(f"   Max Violation:           {feas.max_violation:.2e}")
    lines.append(f"   Max Equality Residual:   {feas.max_equality_residual:.2e}")
    lines.append(f"   Max Inequality Residual: {feas.max_inequality_violation:.2e}")
    lines.append(f"   Max Bound Violation:     {feas.max_bound_violation:.2e}")
    lines.append(f"   Max Integrality Gap:     {feas.max_integrality_residual:.2e}")
    lines.append(sub_separator)

    # Economics Section
    econ = report.economics
    lines.append("2. ECONOMIC VALUATION & COST BREAKDOWN")
    lines.append(f"   TOTAL RECONSTRUCTED COST: KSh {econ.total_cost:,.2f}")
    lines.append(f"   Reconstruction Residual:  {econ.reconstruction_residual:.2e}")
    lines.append("   Components:")
    shares = econ.percentage_shares
    lines.append(f"     * Variable Energy:      KSh {econ.energy_variable:12,.2f} ({shares.get('energy_variable', 0.0):6.2f}%)")
    lines.append(f"     * Fixed Online Energy:  KSh {econ.energy_fixed:12,.2f} ({shares.get('energy_fixed', 0.0):6.2f}%)")
    lines.append(f"     * Demand Charge:        KSh {econ.demand_charge:12,.2f} ({shares.get('demand_charge', 0.0):6.2f}%)")
    lines.append(f"     * Material Purchases:   KSh {econ.purchase:12,.2f} ({shares.get('purchase', 0.0):6.2f}%)")
    lines.append(f"     * Machine Setups:       KSh {econ.startup:12,.2f} ({shares.get('startup', 0.0):6.2f}%)")
    lines.append(f"     * Inventory Holding:    KSh {econ.holding:12,.2f} ({shares.get('holding', 0.0):6.2f}%)")
    lines.append(f"     * Demand Shortfall:     KSh {econ.shortfall:12,.2f} ({shares.get('shortfall', 0.0):6.2f}%)")
    lines.append(f"     * Fixed Facility Fee:   KSh {econ.fixed_charge:12,.2f} ({shares.get('fixed_charge', 0.0):6.2f}%)")
    lines.append(sub_separator)

    # Operational Highlights
    lines.append("3. OPERATIONAL HIGHLIGHTS & BOTTLENECKS")
    if report.peak_setting_periods:
        periods_str = ", ".join(str(p) for p in report.peak_setting_periods)
        lines.append(f"   Peak-Setting Intervals: Periods [{periods_str}]")
    lines.append("   Machine Utilization:")
    for m_id, m_ops in report.operations.items():
        lines.append(f"     * Machine '{m_id}': Avg Util: {m_ops.average_utilization*100:5.1f}% | Operating: {m_ops.operating_hours:4.1f}h | Startups: {m_ops.total_startups}")

    binding_count = len(report.binding_constraints)
    lines.append(f"   Active / Binding Constraints: {binding_count} rows")
    for bc in report.binding_constraints[:5]:
        lines.append(f"     - [{bc.category}] {bc.equation_id}: {bc.state} (LHS={bc.lhs_value:.2f}, RHS={bc.rhs_value:.2f}, slack={bc.slack:.2e})")
    if binding_count > 5:
        lines.append(f"     ... and {binding_count - 5} more binding constraints.")
    lines.append(sub_separator)

    # Resource Flow Balance
    lines.append("4. MATERIAL FLOW & MASS BALANCE ACCOUNTING")
    for r_id, flow in report.resource_flows.items():
        lines.append(f"   * Resource '{r_id}': Initial={flow.initial_stock:.1f} + Receipts={flow.total_receipts:.1f} + Produced={flow.total_produced:.1f} - Consumed={flow.total_consumed:.1f} - Shipped={flow.total_shipped:.1f} = Final={flow.final_stock:.1f} (Residual: {flow.conservation_residual:.2e})")
    lines.append(separator)

    return chr(10).join(lines)
