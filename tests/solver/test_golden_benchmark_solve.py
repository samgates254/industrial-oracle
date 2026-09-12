import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for solving the Micro-Factory Golden Benchmark with HiGHS:
Asserts optimal solution (x1=20, x2=20, PeakKVA=12.5, Z*=6550 KSh).
"""

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


class TestGoldenBenchmarkSolve(unittest.TestCase):
    """Golden reference solve against analytical truth."""

    def test_golden_micro_factory_solve(self):
        """Recover analytical truth: x1=20, x2=20, PeakKVA=12.5, Z*=6550.00 KSh."""
        resources = [
            Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
            Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        ]
        processes = [
            Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.90})
        ]
        machines = [
            Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=0.0, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})
        ]
        time_horizon = TimeHorizon(
            num_periods=2,
            delta_t=1.0,
            tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
        )
        economics = Economics(
            energy_tariffs=EnergyTariffs(c_peak=20.0, c_offpeak=10.0, c_shoulder=0.0),
            demand_charge_rate=500.0,
            fixed_charge=0.0,
            purchase_costs={},
            setup_costs={},
            holding_costs={},
            penalty_costs={},
        )
        electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        demand = [DemandOrder(resource_id="FIN", period=2, quantity=36.0)]

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
        factory = normalize_factory(factory_raw)
        model = ModelCompiler.compile(factory)
        reg = model.variable_registry

        solver = HiGHSSolver()
        result = solver.solve(model)

        self.assertEqual(result.status, SolverStatus.OPTIMAL)
        self.assertAlmostEqual(result.objective_value, 6550.00, delta=1e-6)

        # Extract variable values via symbolic registry
        x1_val = result.get_value("x", ("M", "P", 1), reg)
        x2_val = result.get_value("x", ("M", "P", 2), reg)
        peak_val = result.get_value("PeakKVA", (), reg)
        z1_val = result.get_value("z", ("M", 1), reg)
        z2_val = result.get_value("z", ("M", 2), reg)
        s1_val = result.get_value("Startup", ("M", 1), reg)
        s2_val = result.get_value("Startup", ("M", 2), reg)

        self.assertAlmostEqual(x1_val, 20.0, delta=1e-6)
        self.assertAlmostEqual(x2_val, 20.0, delta=1e-6)
        self.assertAlmostEqual(peak_val, 12.5, delta=1e-6)
        self.assertAlmostEqual(z1_val, 1.0, delta=1e-6)
        self.assertAlmostEqual(z2_val, 1.0, delta=1e-6)
        self.assertAlmostEqual(s1_val, 1.0, delta=1e-6)
        self.assertAlmostEqual(s2_val, 0.0, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
