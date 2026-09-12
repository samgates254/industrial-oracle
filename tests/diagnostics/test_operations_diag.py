import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for machine operations diagnostics: utilization and startups."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.operations import compute_machine_operations
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestOperationsDiagnostics(unittest.TestCase):
    """Machine operational metrics tests."""

    def test_micro_factory_machine_operations(self):
        """In Micro-Factory: Cap=50, x1=20, x2=20 => U1=40%, U2=40%, Startups=1."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        ops = compute_machine_operations(factory, model, res.primal_values)
        self.assertIn("M", ops)
        m_ops = ops["M"]

        self.assertAlmostEqual(m_ops.period_utilization[1], 20.0 / 50.0, delta=1e-6)
        self.assertAlmostEqual(m_ops.period_utilization[2], 20.0 / 50.0, delta=1e-6)
        self.assertAlmostEqual(m_ops.average_utilization, 0.40, delta=1e-6)
        self.assertEqual(m_ops.operating_hours, 2.0)
        self.assertEqual(m_ops.total_startups, 1)


if __name__ == "__main__":
    unittest.main()
