import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for HiGHSSolver adapter: Interface, LP, MILP, Bounds, Residuals, and Infeasible cases."""

import unittest
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.solver.status import SolverStatus


class TestHiGHSAdapter(unittest.TestCase):
    """Verification of HiGHS adapter correctness."""

    def _build_factory(self, demand_qty: float = 36.0, cap_rate: float = 50.0, fixed_charge: float = 0.0):
        resources = [
            Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
            Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        ]
        processes = [
            Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.90})
        ]
        machines = [
            Machine(machine_id="M", capacity_rate=cap_rate, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})
        ]
        time_horizon = TimeHorizon(
            num_periods=2,
            delta_t=1.0,
            tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
        )
        economics = Economics(
            energy_tariffs=EnergyTariffs(c_peak=20.0, c_offpeak=10.0, c_shoulder=0.0),
            demand_charge_rate=500.0,
            fixed_charge=fixed_charge,
            purchase_costs={},
            setup_costs={},
            holding_costs={},
            penalty_costs={},
        )
        electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        demand = [DemandOrder(resource_id="FIN", period=2, quantity=demand_qty)]

        factory_raw = FactoryConfiguration(
            schema_version="0.1.0",
            contract_title="V0.1",
            freeze_vector="(A,A,A,A,B,A,A,A)",
            configuration_policy=ConfigurationPolicy(),
            time_horizon=time_horizon,
            resources=resources,
            processes=processes,
            machines=machines,
            economics=economics,
            electrical_parameters=electrical,
            demand=demand,
        )
        return normalize_factory(factory_raw)

    def test_lp_milp_solve_optimal(self):
        """Test standard solve reaches OPTIMAL."""
        factory = self._build_factory()
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        result = solver.solve(model)

        self.assertEqual(result.status, SolverStatus.OPTIMAL)
        self.assertTrue(result.is_optimal)
        self.assertTrue(result.is_feasible)
        self.assertIsNotNone(result.primal_values)
        self.assertIsNotNone(result.objective_value)

    def test_feasibility_residuals_and_bounds(self):
        """Verify equality residuals, inequality residuals, bounds, and integrality."""
        factory = self._build_factory()
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        result = solver.solve(model)

        y = result.primal_values
        eps = 1e-5

        # 1. Equality residuals: A_eq y == b_eq
        for row in model.A_eq_sparse:
            lhs = sum(val * y[col] for col, val in row.coefficients.items())
            self.assertAlmostEqual(lhs, row.rhs, delta=eps)

        # 2. Inequality residuals: A_ub y <= b_ub
        for row in model.A_ub_sparse:
            lhs = sum(val * y[col] for col, val in row.coefficients.items())
            self.assertLessEqual(lhs, row.rhs + eps)

        # 3. Variable bounds: l <= y <= u
        for j in range(model.num_variables):
            self.assertGreaterEqual(y[j], model.l[j] - eps)
            self.assertLessEqual(y[j], model.u[j] + eps)

        # 4. Integrality: integer variables must be within eps of an integer
        for j in model.integer_indices:
            val = y[j]
            dist_int = abs(val - round(val))
            self.assertLessEqual(dist_int, eps)

    def test_infeasible_model_handling(self):
        """Infeasible model returns normalized INFEASIBLE, not an exception."""
        # Demand of 1000 kg when max capacity across 2 periods is 2 * 50 = 100 kg
        factory = self._build_factory(demand_qty=1000.0, cap_rate=50.0)
        model = ModelCompiler.compile(factory)
        solver = HiGHSSolver()
        result = solver.solve(model)

        self.assertEqual(result.status, SolverStatus.INFEASIBLE)
        self.assertFalse(result.is_optimal)
        self.assertFalse(result.is_feasible)
        self.assertIsNone(result.primal_values)
        self.assertIsNone(result.objective_value)

    def test_fixed_charge_invariance_on_decisions(self):
        """Adding fixed charge F changes Z* by exactly F, leaving y* identical."""
        f_zero = self._build_factory(fixed_charge=0.0)
        f_fixed = self._build_factory(fixed_charge=1000.0)

        m_zero = ModelCompiler.compile(f_zero)
        m_fixed = ModelCompiler.compile(f_fixed)

        solver = HiGHSSolver()
        res_zero = solver.solve(m_zero)
        res_fixed = solver.solve(m_fixed)

        self.assertEqual(res_zero.status, SolverStatus.OPTIMAL)
        self.assertEqual(res_fixed.status, SolverStatus.OPTIMAL)

        # Primal decisions must be identical
        for y0, yF in zip(res_zero.primal_values, res_fixed.primal_values):
            self.assertAlmostEqual(y0, yF, delta=1e-5)

        # Objective increases by exactly 1000.0
        self.assertAlmostEqual(res_fixed.objective_value, res_zero.objective_value + 1000.0, delta=1e-5)


if __name__ == "__main__":
    unittest.main()
