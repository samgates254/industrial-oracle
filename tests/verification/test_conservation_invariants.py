import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar II: Conservation Invariants on decoded variable states."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from .fixtures.analytical_truth_sets import (
    make_asymmetric_dispatch_fixture,
    make_micro_factory_fixture,
    make_multi_stage_supply_chain_fixture,
)


class TestConservationInvariants(unittest.TestCase):
    """Verification of material flow conservation across time."""

    def setUp(self):
        self.solver = HiGHSSolver()

    def _verify_conservation_on_factory(self, factory_raw):
        factory = normalize_factory(factory_raw)
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry
        res = self.solver.solve(model)
        self.assertTrue(res.is_optimal)

        # 1. Canonical matrix residual check: max |A_eq y - b_eq| <= 1e-6
        y = res.primal_values
        for row in model.A_eq_sparse:
            lhs = sum(val * y[col] for col, val in row.coefficients.items())
            self.assertAlmostEqual(lhs, row.rhs, delta=1e-6)

        # 2. Independent material balance calculation from decoded VariableRegistry values
        N_T = factory.time_horizon.num_periods
        for r in factory.resources:
            r_id = r.resource_id

            # Period 1: Inv_{r,1} = InitialStock_r + sum_p (b - a) sum_m x_{m,p,1} + Receipts - Ship
            net_trans_1 = 0.0
            for p in factory.processes:
                b_val = p.output_coefficients.get(r_id, 0.0)
                a_val = p.input_coefficients.get(r_id, 0.0)
                for m_id in factory.indexes.M_p[p.process_id]:
                    net_trans_1 += (b_val - a_val) * res.get_value("x", (m_id, p.process_id, 1), reg)

            receipts_1 = res.get_value("Receipts", (r_id, 1), reg) if r.is_purchasable else 0.0
            ship_1 = res.get_value("Ship", (r_id, 1), reg) if r.category == "FINISHED" else 0.0
            expected_inv_1 = r.initial_stock + net_trans_1 + receipts_1 - ship_1
            decoded_inv_1 = res.get_value("Inv", (r_id, 1), reg)
            self.assertAlmostEqual(decoded_inv_1, expected_inv_1, delta=1e-6)

            # Periods t >= 2: Inv_{r,t} = Inv_{r,t-1} + sum_p (b - a) sum_m x_{m,p,t} + Receipts - Ship
            prev_inv = decoded_inv_1
            for t in range(2, N_T + 1):
                net_trans_t = 0.0
                for p in factory.processes:
                    b_val = p.output_coefficients.get(r_id, 0.0)
                    a_val = p.input_coefficients.get(r_id, 0.0)
                    for m_id in factory.indexes.M_p[p.process_id]:
                        net_trans_t += (b_val - a_val) * res.get_value("x", (m_id, p.process_id, t), reg)

                receipts_t = res.get_value("Receipts", (r_id, t), reg) if r.is_purchasable else 0.0
                ship_t = res.get_value("Ship", (r_id, t), reg) if r.category == "FINISHED" else 0.0
                expected_inv_t = prev_inv + net_trans_t + receipts_t - ship_t
                decoded_inv_t = res.get_value("Inv", (r_id, t), reg)
                self.assertAlmostEqual(decoded_inv_t, expected_inv_t, delta=1e-6)
                prev_inv = decoded_inv_t

    def test_conservation_micro_factory(self):
        self._verify_conservation_on_factory(make_micro_factory_fixture())

    def test_conservation_multi_stage_supply_chain(self):
        self._verify_conservation_on_factory(make_multi_stage_supply_chain_fixture())

    def test_conservation_asymmetric_dispatch(self):
        self._verify_conservation_on_factory(make_asymmetric_dispatch_fixture())


if __name__ == "__main__":
    unittest.main()
