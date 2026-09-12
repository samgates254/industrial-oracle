import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for physical infeasibility evidence generation without artificial IIS claims."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.solver.status import SolverStatus
from industrial_oracle.diagnostics.infeasibility import analyze_infeasibility_evidence
from tests.verification.fixtures.pathological_cases import (
    make_demand_beyond_capacity_fixture,
    make_zero_initial_stock_with_safety_stock_fixture,
)
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestInfeasibilityDiagnostics(unittest.TestCase):
    """Physical evidence extraction for infeasible models."""

    def test_capacity_deficit_evidence(self):
        """Demand beyond capacity produces explicit capacity deficit evidence."""
        factory = normalize_factory(make_demand_beyond_capacity_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)
        self.assertEqual(res.status, SolverStatus.INFEASIBLE)

        evidence = analyze_infeasibility_evidence(factory, is_infeasible=True)
        self.assertTrue(evidence.is_infeasible)
        self.assertEqual(evidence.capacity_deficit, 20.0) # 120 - 100 = 20 kg
        self.assertTrue(any("CAPACITY_EVIDENCE" in msg for msg in evidence.evidence_messages))

    def test_safety_stock_conflict_evidence(self):
        """Unreplenishable safety stock conflict is detected."""
        factory = normalize_factory(make_zero_initial_stock_with_safety_stock_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)
        self.assertEqual(res.status, SolverStatus.INFEASIBLE)

        evidence = analyze_infeasibility_evidence(factory, is_infeasible=True)
        self.assertTrue(evidence.is_infeasible)
        self.assertTrue(any("UNREPLENISHABLE_SAFETY_STOCK_CONFLICT" in msg for msg in evidence.evidence_messages))

    def test_feasible_model_zero_evidence(self):
        """Feasible models produce is_infeasible = False and zero deficit."""
        factory = normalize_factory(make_micro_factory_fixture())
        evidence = analyze_infeasibility_evidence(factory, is_infeasible=False)
        self.assertFalse(evidence.is_infeasible)
        self.assertEqual(evidence.capacity_deficit, 0.0)
        self.assertEqual(len(evidence.evidence_messages), 0)


if __name__ == "__main__":
    unittest.main()
