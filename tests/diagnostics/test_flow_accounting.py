import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for resource flow accounting and mass conservation."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.flow import compute_resource_flows
from tests.verification.fixtures.analytical_truth_sets import (
    make_micro_factory_fixture,
    make_multi_stage_supply_chain_fixture,
)


class TestFlowAccounting(unittest.TestCase):
    """Resource mass flow balance accounting tests."""

    def test_micro_factory_flow_accounting(self):
        """Micro-Factory flow verification."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        flows = compute_resource_flows(factory, model, res.primal_values)

        # RAW: Initial 100, Consumed 40, Final 60, Residual 0.0
        raw_flow = flows["RAW"]
        self.assertEqual(raw_flow.initial_stock, 100.0)
        self.assertEqual(raw_flow.total_consumed, 40.0)
        self.assertEqual(raw_flow.final_stock, 60.0)
        self.assertAlmostEqual(raw_flow.conservation_residual, 0.0, delta=1e-6)

        # FIN: Initial 0, Produced 36, Shipped 36, Final 0, Residual 0.0
        fin_flow = flows["FIN"]
        self.assertEqual(fin_flow.total_produced, 36.0)
        self.assertEqual(fin_flow.total_shipped, 36.0)
        self.assertEqual(fin_flow.final_stock, 0.0)
        self.assertAlmostEqual(fin_flow.conservation_residual, 0.0, delta=1e-6)

    def test_multi_stage_intermediate_balance(self):
        """Multi-stage benchmark: INT_produced = 40 kg, INT_consumed = 40 kg."""
        factory = normalize_factory(make_multi_stage_supply_chain_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        flows = compute_resource_flows(factory, model, res.primal_values)
        int_flow = flows["INT"]

        self.assertEqual(int_flow.total_produced, 40.0)
        self.assertEqual(int_flow.total_consumed, 40.0)
        self.assertEqual(int_flow.final_stock, 0.0)
        self.assertAlmostEqual(int_flow.conservation_residual, 0.0, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
