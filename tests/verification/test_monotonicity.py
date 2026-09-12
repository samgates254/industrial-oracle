import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar IV: Monotonicity and Sensitivity Verifications."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from .fixtures.monotonicity_cases import (
    make_capacity_perturbed_pair,
    make_demand_perturbed_pair,
    make_power_factor_perturbed_pair,
    make_tariff_perturbed_pair,
)


class TestMonotonicity(unittest.TestCase):
    """Verification of physical and economic monotonicity properties."""

    def setUp(self):
        self.solver = HiGHSSolver()

    def test_tariff_monotonicity(self):
        """Pillar IV.1: Tariff increase pi_t' >= pi_t implies Z*(pi') >= Z*(pi)."""
        f_base, f_high = make_tariff_perturbed_pair()
        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_high = ModelCompiler.compile(normalize_factory(f_high))

        res_base = self.solver.solve(m_base)
        res_high = self.solver.solve(m_high)

        self.assertTrue(res_base.is_optimal)
        self.assertTrue(res_high.is_optimal)
        # Optimal cost must monotonically non-decrease
        self.assertGreaterEqual(res_high.objective_value, res_base.objective_value - 1e-6)

    def test_power_factor_monotonicity(self):
        """Pillar IV.2: cos_phi_B < cos_phi_A implies PeakKVA(B) >= PeakKVA(A) (strict when kW > 0)."""
        f_high_pf, f_low_pf = make_power_factor_perturbed_pair() # 0.80 vs 0.60
        m_high_pf = ModelCompiler.compile(normalize_factory(f_high_pf))
        m_low_pf = ModelCompiler.compile(normalize_factory(f_low_pf))

        res_high_pf = self.solver.solve(m_high_pf)
        res_low_pf = self.solver.solve(m_low_pf)

        reg_high = m_high_pf.variable_registry
        reg_low = m_low_pf.variable_registry

        peak_high_pf = res_high_pf.get_value("PeakKVA", (), reg_high)
        peak_low_pf = res_low_pf.get_value("PeakKVA", (), reg_low)

        # Lower power factor must increase apparent power
        self.assertGreater(peak_low_pf, peak_high_pf + 1e-6)
        # At 0.8: PeakKVA = 12.5; at 0.6: PeakKVA = 10 / 0.6 = 16.666667
        self.assertAlmostEqual(peak_high_pf, 12.5, delta=1e-6)
        self.assertAlmostEqual(peak_low_pf, 10.0 / 0.60, delta=1e-6)

    def test_demand_monotonicity(self):
        """Pillar IV.3: Demand' >= Demand implies Z*(Demand') >= Z*(Demand)."""
        f_base, f_high_dmd = make_demand_perturbed_pair() # 36 kg vs 40 kg
        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_high_dmd = ModelCompiler.compile(normalize_factory(f_high_dmd))

        res_base = self.solver.solve(m_base)
        res_high_dmd = self.solver.solve(m_high_dmd)

        self.assertTrue(res_base.is_optimal)
        self.assertTrue(res_high_dmd.is_optimal)
        self.assertGreater(res_high_dmd.objective_value, res_base.objective_value + 1e-6)

    def test_capacity_relaxation_monotonicity(self):
        """Pillar IV.4: Cap_m' >= Cap_m implies feasible region does not shrink: Z*(Cap') <= Z*(Cap)."""
        f_base, f_high_cap = make_capacity_perturbed_pair() # 50 kg/h vs 70 kg/h
        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_high_cap = ModelCompiler.compile(normalize_factory(f_high_cap))

        res_base = self.solver.solve(m_base)
        res_high_cap = self.solver.solve(m_high_cap)

        self.assertTrue(res_base.is_optimal)
        self.assertTrue(res_high_cap.is_optimal)
        self.assertLessEqual(res_high_cap.objective_value, res_base.objective_value + 1e-6)


if __name__ == "__main__":
    unittest.main()
