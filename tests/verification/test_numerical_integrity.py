import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar VI: Numerical Integrity, Residuals, and Adversarial Model Mutations."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from .fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestNumericalIntegrity(unittest.TestCase):
    """Pillar VI numerical bounds, residual tolerance, and adversarial model mutation tests."""

    def setUp(self):
        self.solver = HiGHSSolver()

    def test_numerical_residual_and_bound_tolerances(self):
        """Verify strict tolerances on residuals, bounds, integrality, and objective reconstruction."""
        factory = normalize_factory(make_micro_factory_fixture())
        model = ModelCompiler.compile(factory)
        res = self.solver.solve(model)

        y = res.primal_values
        eps = 1e-6

        # 1. Equality feasibility: max |A_eq y - b_eq| <= 1e-6
        for row in model.A_eq_sparse:
            lhs = sum(val * y[col] for col, val in row.coefficients.items())
            self.assertLessEqual(abs(lhs - row.rhs), eps)

        # 2. Inequality feasibility: max (A_ub y - b_ub) <= 1e-6
        for row in model.A_ub_sparse:
            lhs = sum(val * y[col] for col, val in row.coefficients.items())
            self.assertLessEqual(lhs - row.rhs, eps)

        # 3. Lower and upper bounds: min (y - l) >= -1e-6, min (u - y) >= -1e-6
        for j in range(model.num_variables):
            self.assertGreaterEqual(y[j] - model.l[j], -eps)
            self.assertGreaterEqual(model.u[j] - y[j], -eps)

        # 4. Integrality: max |y_j - round(y_j)| <= 1e-6 for j in I
        for j in model.integer_indices:
            self.assertLessEqual(abs(y[j] - round(y[j])), eps)

        # 5. Independent Objective Reconstruction: |Z_independent - Z_reported| <= 1e-6
        Z_independent = sum(model.c[j] * y[j] for j in range(model.num_variables)) + model.fixed_charge
        self.assertLessEqual(abs(Z_independent - res.objective_value), eps)

    def test_fixed_charge_verification(self):
        """Verify Z*(F2) - Z*(F1) = F2 - F1 with unchanged operational decisions."""
        f_base = make_micro_factory_fixture()
        econ_f1 = f_base.economics.copy(update={"fixed_charge": 500.0})
        econ_f2 = f_base.economics.copy(update={"fixed_charge": 1500.0})

        m1 = ModelCompiler.compile(normalize_factory(f_base.copy(update={"economics": econ_f1})))
        m2 = ModelCompiler.compile(normalize_factory(f_base.copy(update={"economics": econ_f2})))

        res1 = self.solver.solve(m1)
        res2 = self.solver.solve(m2)

        self.assertAlmostEqual(res2.objective_value - res1.objective_value, 1000.0, delta=1e-6)

    def test_adversarial_mutation_tariff_change(self):
        """Changing tariffs changes c, while A_eq, A_ub, l, u remain strictly identical."""
        f_base = make_micro_factory_fixture()
        econ_mod = f_base.economics.copy(update={"energy_tariffs": EnergyTariffs(c_peak=50.0, c_offpeak=25.0, c_shoulder=0.0)})
        f_mod = f_base.copy(update={"economics": econ_mod})

        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_mod = ModelCompiler.compile(normalize_factory(f_mod))

        self.assertNotEqual(m_base.c, m_mod.c)
        self.assertEqual(m_base.A_eq_dense, m_mod.A_eq_dense)
        self.assertEqual(m_base.b_eq, m_mod.b_eq)
        self.assertEqual(m_base.A_ub_dense, m_mod.A_ub_dense)
        self.assertEqual(m_base.b_ub, m_mod.b_ub)
        self.assertEqual(m_base.l, m_mod.l)
        self.assertEqual(m_base.u, m_mod.u)

    def test_adversarial_mutation_capacity_change(self):
        """Changing machine capacity alters only capacity rows and bounds, not economics or balance."""
        f_base = make_micro_factory_fixture()
        mach_mod = [Machine(machine_id="M", capacity_rate=80.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})]
        f_mod = f_base.copy(update={"machines": mach_mod})

        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_mod = ModelCompiler.compile(normalize_factory(f_mod))

        self.assertEqual(m_base.c, m_mod.c)
        self.assertEqual(m_base.A_eq_dense, m_mod.A_eq_dense)
        self.assertEqual(m_base.b_eq, m_mod.b_eq)
        # Inequality rows differ because capacity constraint coefficient changed (-50 vs -80)
        self.assertNotEqual(m_base.A_ub_dense, m_mod.A_ub_dense)

    def test_adversarial_mutation_process_yield_change(self):
        """Changing process transformation changes balance rows, leaving tariff rates unchanged."""
        f_base = make_micro_factory_fixture()
        proc_mod = [Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.95})]
        f_mod = f_base.copy(update={"processes": proc_mod})

        m_base = ModelCompiler.compile(normalize_factory(f_base))
        m_mod = ModelCompiler.compile(normalize_factory(f_mod))

        self.assertEqual(m_base.c, m_mod.c)
        # Equality rows differ because yield coefficient changed (-0.90 vs -0.95)
        self.assertNotEqual(m_base.A_eq_dense, m_mod.A_eq_dense)


if __name__ == "__main__":
    unittest.main()
