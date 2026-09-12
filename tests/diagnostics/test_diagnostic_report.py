import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""End-to-end DiagnosticReport generation, determinism, and immutability audit."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.engine import DiagnosticsEngine
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestDiagnosticReport(unittest.TestCase):
    """Master report orchestration and non-mutation audit."""

    def setUp(self):
        self.factory = normalize_factory(make_micro_factory_fixture())
        self.model = ModelCompiler.compile(self.factory)
        self.solver = HiGHSSolver()
        self.result = self.solver.solve(self.model)

    def test_end_to_end_report_generation(self):
        """Verify complete report generation on optimal Micro-Factory."""
        report = DiagnosticsEngine.analyze(self.factory, self.model, self.result)

        self.assertEqual(report.solver_status, "OPTIMAL")
        self.assertTrue(report.feasibility.is_verified_feasible)
        self.assertEqual(report.peak_setting_periods, (1, 2))
        self.assertAlmostEqual(report.economics.total_cost, 6550.0, delta=1e-6)
        self.assertIn("M", report.operations)
        self.assertIn("RAW", report.resource_flows)
        self.assertFalse(report.infeasibility.is_infeasible)

    def test_non_mutation_audit(self):
        """DiagnosticsEngine must not modify CanonicalModel or SolverResult."""
        model_c_before = tuple(self.model.c)
        model_l_before = tuple(self.model.l)
        model_u_before = tuple(self.model.u)
        result_primal_before = tuple(self.result.primal_values)
        result_obj_before = self.result.objective_value

        report = DiagnosticsEngine.analyze(self.factory, self.model, self.result)

        self.assertEqual(self.model.c, model_c_before)
        self.assertEqual(self.model.l, model_l_before)
        self.assertEqual(self.model.u, model_u_before)
        self.assertEqual(self.result.primal_values, result_primal_before)
        self.assertEqual(self.result.objective_value, result_obj_before)

    def test_determinism_audit(self):
        """Running analyze() twice on identical inputs yields equivalent reports."""
        r1 = DiagnosticsEngine.analyze(self.factory, self.model, self.result)
        r2 = DiagnosticsEngine.analyze(self.factory, self.model, self.result)

        self.assertEqual(r1.feasibility, r2.feasibility)
        self.assertEqual(r1.binding_constraints, r2.binding_constraints)
        self.assertEqual(r1.peak_setting_periods, r2.peak_setting_periods)
        self.assertEqual(r1.economics, r2.economics)
        self.assertEqual(r1.operations, r2.operations)
        self.assertEqual(r1.resource_flows, r2.resource_flows)
        self.assertEqual(r1.infeasibility, r2.infeasibility)

    def test_immutability_audit(self):
        """Attempted mutation of report structures raises exceptions."""
        report = DiagnosticsEngine.analyze(self.factory, self.model, self.result)

        # 1. Attribute reassignment on root report
        with self.assertRaises(Exception):
            report.solver_status = "MUTATED"

        # 2. Mutation on operations mapping
        with self.assertRaises(TypeError):
            report.operations["M"] = None

        # 3. Mutation on resource_flows mapping
        with self.assertRaises(TypeError):
            report.resource_flows["RAW"] = None

        # 4. Mutation on percentage_shares mapping
        with self.assertRaises(TypeError):
            report.economics.percentage_shares["demand_charge"] = 50.0


if __name__ == "__main__":
    unittest.main()
