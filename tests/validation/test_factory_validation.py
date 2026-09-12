import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for FactoryConfiguration validation & Factory-X regression."""

import unittest
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.factory import (
    ConfigurationPolicy,
    FactoryConfiguration,
)
from industrial_oracle.domain.machines import Machine
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.validation.exceptions import PhysicalValidationError
from industrial_oracle.validation.physical import validate_factory


class TestFactoryValidation(unittest.TestCase):
    """Unit tests for Factory-level validation."""

    def _build_factory_x(self):
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

        return FactoryConfiguration(
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

    def test_factory_x_regression_accept(self):
        """Verify that complete Factory-X validates with zero errors."""
        factory = self._build_factory_x()
        validate_factory(factory)

    def test_duplicate_resource_id_rejected(self):
        factory = self._build_factory_x()
        dup_res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=10.0,
            safety_stock=0.0,
            max_storage=100.0,
            is_purchasable=True,
        )
        factory_dup = factory.copy(update={"resources": factory.resources + [dup_res]})
        with self.assertRaises(PhysicalValidationError):
            validate_factory(factory_dup)

    def test_duplicate_process_id_rejected(self):
        factory = self._build_factory_x()
        dup_proc = Process(
            process_id="P1",
            input_coefficients={"RAW": 1.0},
            output_coefficients={"INTERMEDIATE": 0.9},
        )
        factory_dup = factory.copy(update={"processes": factory.processes + [dup_proc]})
        with self.assertRaises(PhysicalValidationError):
            validate_factory(factory_dup)

    def test_duplicate_machine_id_rejected(self):
        factory = self._build_factory_x()
        dup_mach = Machine(
            machine_id="M1",
            capacity_rate=50.0,
            min_load_rate=10.0,
            fixed_power=2.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        factory_dup = factory.copy(update={"machines": factory.machines + [dup_mach]})
        with self.assertRaises(PhysicalValidationError):
            validate_factory(factory_dup)


if __name__ == "__main__":
    unittest.main()
