import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for compilation of multi-machine, multi-process complex factory networks."""

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


class TestComplexFactoryCompilation(unittest.TestCase):
    """Multi-machine and multi-process network compilation tests."""

    def test_factory_x_matrix_compilation(self):
        """Verify full Factory-X (2 machines, 2 processes, 3 resources, 24 periods)."""
        resources = [
            Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=500.0, safety_stock=50.0, max_storage=1000.0, is_purchasable=True),
            Resource(resource_id="INTERMEDIATE", category=ResourceCategory.WIP, initial_stock=0.0, safety_stock=0.0, max_storage=500.0, is_purchasable=False),
            Resource(resource_id="FINISHED", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        ]
        processes = [
            Process(process_id="P1", input_coefficients={"RAW": 1.0}, output_coefficients={"INTERMEDIATE": 0.90}),
            Process(process_id="P2", input_coefficients={"INTERMEDIATE": 1.0}, output_coefficients={"FINISHED": 0.95}),
        ]
        machines = [
            Machine(machine_id="M1", capacity_rate=100.0, min_load_rate=20.0, fixed_power=5.0, initial_state=0, compatible_processes=["P1"], variable_energy={"P1": 0.5}),
            Machine(machine_id="M2", capacity_rate=80.0, min_load_rate=15.0, fixed_power=4.0, initial_state=0, compatible_processes=["P2"], variable_energy={"P2": 0.7}),
        ]
        time_horizon = TimeHorizon(
            num_periods=24,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[9, 10, 11, 12, 18, 19, 20],
                offpeak_periods=[1, 2, 3, 4, 5, 6, 23, 24],
                shoulder_periods=[7, 8, 13, 14, 15, 16, 17, 21, 22],
            ),
        )
        economics = Economics(
            energy_tariffs=EnergyTariffs(c_peak=30.0, c_offpeak=10.0, c_shoulder=20.0),
            demand_charge_rate=500.0,
            fixed_charge=1000.0,
            purchase_costs={"RAW": 80.0},
            setup_costs={"M1": 500.0, "M2": 700.0},
            holding_costs={"RAW": 2.0, "INTERMEDIATE": 3.0, "FINISHED": 4.0},
            penalty_costs={"FINISHED": 200.0},
        )
        electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        demand = [DemandOrder(resource_id="FINISHED", period=24, quantity=150.0)]

        factory_raw = FactoryConfiguration(
            schema_version="0.1.0",
            contract_title="V0.1",
            freeze_vector="(A,A,A,A,B,A,A,A)",
            configuration_policy=ConfigurationPolicy(allow_demand_shortfall=False),
            time_horizon=time_horizon,
            resources=resources,
            processes=processes,
            machines=machines,
            economics=economics,
            electrical_parameters=electrical,
            demand=demand,
        )
        norm_factory = normalize_factory(factory_raw)
        model = ModelCompiler.compile(norm_factory)

        # Audit Factory-X Variable count:
        # N_T=24, K=2, |M|=2, |R|=3, |R_purch|=1, |R_fin|=1, soft=0
        # N_vars = 24 * (2 + 4 + 3 + 1 + 1) + 1 = 24 * 11 + 1 = 264 + 1 = 265
        self.assertEqual(model.num_variables, 265)

        # Audit Factory-X Row counts:
        # M_eq = |R| * N_T + |R_fin| * N_T = 3 * 24 + 1 * 24 = 72 + 24 = 96
        self.assertEqual(model.num_equalities, 96)

        # M_ub = (5 * |M| + 1) * N_T = (5*2 + 1) * 24 = 11 * 24 = 264
        self.assertEqual(model.num_inequalities, 264)

        # Bounds consistency
        for j in range(model.num_variables):
            self.assertLessEqual(model.l[j], model.u[j])


if __name__ == "__main__":
    unittest.main()
