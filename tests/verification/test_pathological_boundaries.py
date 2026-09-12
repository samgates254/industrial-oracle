import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar III: Pathological Boundary Conditions."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.solver.status import SolverStatus
from .fixtures.pathological_cases import (
    make_demand_beyond_capacity_fixture,
    make_exact_capacity_bottleneck_fixture,
    make_single_period_demand_spike_fixture,
    make_zero_initial_stock_with_safety_stock_fixture,
)


class TestPathologicalBoundaries(unittest.TestCase):
    """Adversarial boundary condition tests."""

    def setUp(self):
        self.solver = HiGHSSolver()

    def test_exact_capacity_bottleneck(self):
        """Pillar III.1: Demand exactly saturated at 100% capacity -> OPTIMAL."""
        factory = normalize_factory(make_exact_capacity_bottleneck_fixture())
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.OPTIMAL)
        # All available machine capacity must be exactly consumed: 50 kg in t=1, 50 kg in t=2
        x1 = res.get_value("x", ("M", "P", 1), reg)
        x2 = res.get_value("x", ("M", "P", 2), reg)
        self.assertAlmostEqual(x1, 50.0, delta=1e-6)
        self.assertAlmostEqual(x2, 50.0, delta=1e-6)

    def test_demand_beyond_capacity(self):
        """Pillar III.2: Demand exceeds physical capacity -> INFEASIBLE."""
        factory = normalize_factory(make_demand_beyond_capacity_fixture())
        model = ModelCompiler.compile(factory)
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.INFEASIBLE)
        self.assertFalse(res.is_optimal)

    def test_zero_initial_stock_with_safety_stock(self):
        """Pillar III.3: InitialStock = 0, SafetyStock = 20, non-purchasable -> INFEASIBLE."""
        factory = normalize_factory(make_zero_initial_stock_with_safety_stock_fixture())
        model = ModelCompiler.compile(factory)
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.INFEASIBLE)
        self.assertFalse(res.is_optimal)

    def test_single_period_demand_spike_production_shift(self):
        """Pillar III.4: Demand spike at t=2 exceeds single-period cap -> Shifts to t=1.
        Under peak-kVA penalty, the global optimum balances load evenly (x1=40, x2=40) to minimize max(kVA_1, kVA_2)
        at 20.0 kVA rather than taking the asymmetric hit at 25.0 kVA."""
        factory = normalize_factory(make_single_period_demand_spike_fixture())
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.OPTIMAL)
        x1 = res.get_value("x", ("M", "P", 1), reg)
        x2 = res.get_value("x", ("M", "P", 2), reg)
        inv1 = res.get_value("Inv", ("FIN", 1), reg)
        peak = res.get_value("PeakKVA", (), reg)

        # Proves inventory carryover: 40 kg produced in period 1 is stored in FIN inventory
        self.assertAlmostEqual(x1, 40.0, delta=1e-6)
        self.assertAlmostEqual(x2, 40.0, delta=1e-6)
        self.assertAlmostEqual(inv1, 40.0, delta=1e-6)
        self.assertAlmostEqual(peak, 20.0, delta=1e-6)
        self.assertAlmostEqual(res.objective_value, 2400.0, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
