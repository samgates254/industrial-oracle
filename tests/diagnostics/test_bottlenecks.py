import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for binding constraint identification and peak-setting period detection."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.bottlenecks import detect_peak_setting_periods, extract_binding_constraints
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture
from tests.verification.fixtures.pathological_cases import make_exact_capacity_bottleneck_fixture


class TestBottleneckDiagnostics(unittest.TestCase):
    """Binding constraint extraction and peak-setting detection tests."""

    def test_peak_setting_periods_micro_factory(self):
        """In Micro-Factory, load balancing makes BOTH period 1 and 2 peak-setting at 12.5 kVA."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        peak_periods = detect_peak_setting_periods(factory, model, res.primal_values)
        self.assertEqual(peak_periods, (1, 2))

    def test_binding_inequalities_vs_satisfied_equalities(self):
        """Verify clear separation between SATISFIED_EQUALITY and BINDING inequalities."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        records = extract_binding_constraints(model, res.primal_values)

        eq_records = [r for r in records if r.state == "SATISFIED_EQUALITY"]
        binding_ub = [r for r in records if r.state == "BINDING"]

        self.assertEqual(len(eq_records), model.num_equalities)
        # Peak constraints are binding: EQ-PEAK-001_1 and EQ-PEAK-001_2
        peak_binding = [r for r in binding_ub if r.category == "PEAK"]
        self.assertEqual(len(peak_binding), 2)
        for r in peak_binding:
            self.assertAlmostEqual(r.slack, 0.0, delta=1e-6)

    def test_binding_capacity_at_exact_bottleneck(self):
        """In 100% capacity saturation fixture, EQ-CAP rows are binding with slack = 0.0."""
        factory = normalize_factory(make_exact_capacity_bottleneck_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        records = extract_binding_constraints(model, res.primal_values)
        cap_binding = [r for r in records if r.category == "CAPACITY" and r.state == "BINDING"]

        self.assertEqual(len(cap_binding), 2)
        for r in cap_binding:
            self.assertAlmostEqual(r.slack, 0.0, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
