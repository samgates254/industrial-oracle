import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar I: Analytical Truth Sets with independently derived expected values."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.solver.status import SolverStatus
from .fixtures.analytical_truth_sets import (
    make_asymmetric_dispatch_fixture,
    make_micro_factory_fixture,
    make_multi_stage_supply_chain_fixture,
)


class TestAnalyticalTruthSets(unittest.TestCase):
    """Verification of solver solutions against independent hand-derived analytical optima."""

    def setUp(self):
        self.solver = HiGHSSolver()

    def test_pillar1_1_micro_factory_regression(self):
        """Pillar I.1: Two-Period Micro-Factory Analytical Truth."""
        # Hand-derived analytical truth:
        # x_1 = 20.0, x_2 = 20.0, PeakKVA = 12.5, Z* = 6550.00 KSh
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.OPTIMAL)
        self.assertAlmostEqual(res.objective_value, 6550.00, delta=1e-6)

        # Computational verification confirms agreement with the independently derived analytical optimum
        self.assertAlmostEqual(res.get_value("x", ("M", "P", 1), reg), 20.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("x", ("M", "P", 2), reg), 20.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("PeakKVA", (), reg), 12.5, delta=1e-6)
        self.assertAlmostEqual(res.get_value("z", ("M", 1), reg), 1.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("z", ("M", 2), reg), 1.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Startup", ("M", 1), reg), 1.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Startup", ("M", 2), reg), 0.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Inv", ("RAW", 1), reg), 80.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Inv", ("RAW", 2), reg), 60.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Inv", ("FIN", 1), reg), 18.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Inv", ("FIN", 2), reg), 0.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Ship", ("FIN", 1), reg), 0.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("Ship", ("FIN", 2), reg), 36.0, delta=1e-6)

    def test_pillar1_2_multi_stage_supply_chain(self):
        """Pillar I.2: Multi-Stage Supply Chain (RAW -> INT -> FIN)."""
        # Hand-derived analytical truth:
        # x_M1_1 = 40.0, x_M1_2 = 0.0
        # x_M2_1 = 0.0, x_M2_2 = 40.0
        # Inv_INT_1 = 40.0, Inv_INT_2 = 0.0
        # PeakKVA = 20.0, Z* = 2400.00 KSh
        factory = normalize_factory(make_multi_stage_supply_chain_fixture())
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.OPTIMAL)
        self.assertAlmostEqual(res.objective_value, 2400.00, delta=1e-6)

        # Computational verification confirms agreement with the independently derived analytical optimum
        # Total P1 production across both periods equals 40.0
        prod_p1_1 = res.get_value("x", ("M1", "P1", 1), reg)
        prod_p1_2 = res.get_value("x", ("M1", "P1", 2), reg)
        self.assertAlmostEqual(prod_p1_1 + prod_p1_2, 40.0, delta=1e-6)

        # Total P2 production across both periods equals 40.0
        prod_p2_1 = res.get_value("x", ("M2", "P2", 1), reg)
        prod_p2_2 = res.get_value("x", ("M2", "P2", 2), reg)
        self.assertAlmostEqual(prod_p2_1 + prod_p2_2, 40.0, delta=1e-6)

        # Inventory balance and demand fulfillment
        # FIN demand is 40 at period 2
        inv_int_1 = res.get_value("Inv", ("INT", 1), reg)
        inv_int_2 = res.get_value("Inv", ("INT", 2), reg)
        self.assertAlmostEqual(inv_int_1, prod_p1_1 - prod_p2_1, delta=1e-6)
        self.assertAlmostEqual(inv_int_2, inv_int_1 + prod_p1_2 - prod_p2_2, delta=1e-6)

        # PeakKVA check
        self.assertAlmostEqual(res.get_value("PeakKVA", (), reg), 20.0, delta=1e-6)

    def test_pillar1_3_asymmetric_dispatch(self):
        """Pillar I.3: Asymmetric Multi-Machine Dispatch (M1 efficient, M2 inefficient)."""
        # Hand-derived analytical truth:
        # Cap_M1 = 30.0 (cheaper: 0.2 kWh/kg), Cap_M2 = 30.0 (expensive: 0.8 kWh/kg)
        # Demand = 36.0 kg => x_M1 = 30.0 (max capacity), x_M2 = 6.0
        # PeakKVA = 0.2*30 + 0.8*6 = 10.8 kVA
        # Z* = 10*(10.8) + 100*(10.8) = 1188.00 KSh
        factory = normalize_factory(make_asymmetric_dispatch_fixture())
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)

        self.assertEqual(res.status, SolverStatus.OPTIMAL)
        self.assertAlmostEqual(res.objective_value, 1188.00, delta=1e-6)

        # Computational verification confirms agreement with the independently derived analytical optimum
        self.assertAlmostEqual(res.get_value("x", ("M1", "P", 1), reg), 30.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("x", ("M2", "P", 1), reg), 6.0, delta=1e-6)
        self.assertAlmostEqual(res.get_value("PeakKVA", (), reg), 10.8, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
