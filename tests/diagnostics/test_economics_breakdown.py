import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for economic cost decomposition and percentage shares."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.economics import decompose_economic_costs
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestEconomicsBreakdown(unittest.TestCase):
    """Cost decomposition and percentage share tests."""

    def test_micro_factory_cost_breakdown(self):
        """Micro-Factory expected: Z_energy=300, Z_demand=6250, Z=6550, shares ~4.58% and 95.42%."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        breakdown = decompose_economic_costs(factory, model, res.primal_values, res.objective_value)

        self.assertAlmostEqual(breakdown.energy_variable, 300.0, delta=1e-6)
        self.assertAlmostEqual(breakdown.demand_charge, 6250.0, delta=1e-6)
        self.assertAlmostEqual(breakdown.total_cost, 6550.0, delta=1e-6)
        self.assertAlmostEqual(breakdown.reconstruction_residual, 0.0, delta=1e-6)

        # Shares
        share_energy = breakdown.percentage_shares["energy_variable"]
        share_demand = breakdown.percentage_shares["demand_charge"]
        self.assertAlmostEqual(share_energy, (300.0 / 6550.0) * 100.0, delta=1e-2)
        self.assertAlmostEqual(share_demand, (6250.0 / 6550.0) * 100.0, delta=1e-2)
        self.assertAlmostEqual(share_energy + share_demand, 100.0, delta=1e-2)

    def test_exact_sum_components(self):
        """Verify Z_total == sum(all_components) + fixed_charge within 1e-6."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        res = solver.solve(model)

        b = decompose_economic_costs(factory, model, res.primal_values, res.objective_value)
        sum_components = (
            b.energy_variable + b.energy_fixed + b.demand_charge +
            b.purchase + b.startup + b.holding + b.shortfall + b.fixed_charge
        )
        self.assertAlmostEqual(b.total_cost, sum_components, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
