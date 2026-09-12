import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for feasibility diagnostics: residuals, bounds, integrality, perturbation."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.feasibility import compute_feasibility_metrics
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestFeasibilityDiagnostics(unittest.TestCase):
    """Feasibility residual calculation and verification tests."""

    def setUp(self):
        self.factory = normalize_factory(make_micro_factory_fixture())
        self.model = ModelCompiler.compile(self.factory)
        self.solver = HiGHSSolver()
        self.result = self.solver.solve(self.model)

    def test_optimal_micro_factory_residuals(self):
        """Verify that optimal solution satisfies all tolerances <= 1e-6."""
        metrics = compute_feasibility_metrics(self.model, self.result.primal_values)

        self.assertTrue(metrics.is_verified_feasible)
        self.assertLessEqual(metrics.max_equality_residual, 1e-6)
        self.assertLessEqual(metrics.max_inequality_violation, 1e-6)
        self.assertLessEqual(metrics.max_bound_violation, 1e-6)
        self.assertLessEqual(metrics.max_integrality_residual, 1e-6)
        self.assertLessEqual(metrics.max_violation, 1e-6)

    def test_artificially_perturbed_candidate_produces_violation(self):
        """Perturbing primal solution causes explicit feasibility failure."""
        perturbed = list(self.result.primal_values)
        # Violate first equality by perturbing x1
        perturbed[0] += 5.0

        metrics = compute_feasibility_metrics(self.model, perturbed)
        self.assertFalse(metrics.is_verified_feasible)
        self.assertGreater(metrics.max_violation, 1.0)
        self.assertGreater(metrics.max_equality_residual, 1.0)

    def test_integrality_violation_detection(self):
        """Non-integer value on binary variable flags integrality failure."""
        perturbed = list(self.result.primal_values)
        j_z1 = self.model.variable_registry.get_index("z", ("M", 1))
        perturbed[j_z1] = 0.5  # Fractional on integer variable

        metrics = compute_feasibility_metrics(self.model, perturbed)
        self.assertFalse(metrics.is_verified_feasible)
        self.assertAlmostEqual(metrics.max_integrality_residual, 0.5, delta=1e-6)

    def test_none_primal_values_handling(self):
        """Infeasible runs with None primal values return non-verified metrics without crashing."""
        metrics = compute_feasibility_metrics(self.model, None)
        self.assertFalse(metrics.is_verified_feasible)
        self.assertEqual(metrics.max_violation, 0.0)


if __name__ == "__main__":
    unittest.main()
