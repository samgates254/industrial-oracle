import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for complete FactoryConfiguration domain root."""

import unittest
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.factory import ConfigurationPolicy, FactoryConfiguration


class TestFactoryConfiguration(unittest.TestCase):
    """Factory configuration representation tests."""

    def test_represent_factory_x(self):
        """Test 7: Complete representation of Factory-X."""
        resources = [
            Resource(
                resource_id="RAW",
                category=ResourceCategory.RAW,
                initial_stock=500.0,
                safety_stock=50.0,
                max_storage=1000.0,
                is_purchasable=True,
            ),
            Resource(
                resource_id="INTERMEDIATE",
                category=ResourceCategory.WIP,
                initial_stock=0.0,
                safety_stock=0.0,
                max_storage=500.0,
                is_purchasable=False,
            ),
            Resource(
                resource_id="FINISHED",
                category=ResourceCategory.FINISHED,
                initial_stock=0.0,
                safety_stock=0.0,
                max_storage=1000.0,
                is_purchasable=False,
            ),
        ]

        processes = [
            Process(
                process_id="P1",
                input_coefficients={"RAW": 1.0},
                output_coefficients={"INTERMEDIATE": 0.90},
            ),
            Process(
                process_id="P2",
                input_coefficients={"INTERMEDIATE": 1.0},
                output_coefficients={"FINISHED": 0.95},
            ),
        ]

        machines = [
            Machine(
                machine_id="M1",
                capacity_rate=100.0,
                min_load_rate=20.0,
                fixed_power=5.0,
                initial_state=0,
                compatible_processes=["P1"],
                variable_energy={"P1": 0.5},
            ),
            Machine(
                machine_id="M2",
                capacity_rate=80.0,
                min_load_rate=15.0,
                fixed_power=4.0,
                initial_state=0,
                compatible_processes=["P2"],
                variable_energy={"P2": 0.7},
            ),
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
            energy_tariffs=EnergyTariffs(
                c_peak=30.0,
                c_offpeak=10.0,
                c_shoulder=20.0,
            ),
            demand_charge_rate=500.0,
            fixed_charge=1000.0,
            purchase_costs={"RAW": 80.0},
            setup_costs={"M1": 500.0, "M2": 700.0},
            holding_costs={"RAW": 2.0, "INTERMEDIATE": 3.0, "FINISHED": 4.0},
            penalty_costs={"FINISHED": 200.0},
        )

        electrical = ElectricalParameters(
            power_factor=0.80,
            contract_limit_kva=100.0,
        )

        demand = [
            DemandOrder(
                resource_id="FINISHED",
                period=24,
                quantity=150.0,
            )
        ]

        factory = FactoryConfiguration(
            schema_version="0.1.0",
            contract_title="INDUSTRIAL_COST_OPTIMIZATION_ORACLE_V0.1",
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

        self.assertEqual(len(factory.resources), 3)
        self.assertEqual(len(factory.processes), 2)
        self.assertEqual(len(factory.machines), 2)
        self.assertEqual(factory.time_horizon.num_periods, 24)
        self.assertEqual(factory.demand[0].quantity, 150.0)
        self.assertFalse(factory.configuration_policy.allow_demand_shortfall)
        self.assertEqual(factory.configuration_policy.base_currency, "KSh")


if __name__ == "__main__":
    unittest.main()
