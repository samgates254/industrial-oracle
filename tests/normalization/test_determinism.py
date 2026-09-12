import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for normalization determinism and semantic preservation."""

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


class TestNormalizationDeterminism(unittest.TestCase):
    """Deterministic normalization and semantic preservation tests."""

    def _make_factory(self):
        resources = [
            Resource(
                resource_id="RAW_Z",
                category=ResourceCategory.RAW,
                initial_stock=100.0,
                safety_stock=10.0,
                max_storage=500.0,
                is_purchasable=True,
            ),
            Resource(
                resource_id="RAW_A",
                category=ResourceCategory.RAW,
                initial_stock=200.0,
                safety_stock=20.0,
                max_storage=600.0,
                is_purchasable=True,
            ),
        ]
        processes = [
            Process(
                process_id="P2",
                input_coefficients={"RAW_Z": 1.0},
                output_coefficients={"RAW_A": 0.9},
            ),
            Process(
                process_id="P1",
                input_coefficients={"RAW_A": 1.0},
                output_coefficients={"RAW_Z": 0.95},
            ),
        ]
        machines = [
            Machine(
                machine_id="M2",
                capacity_rate=80.0,
                min_load_rate=10.0,
                fixed_power=2.0,
                initial_state=0,
                compatible_processes=["P2"],
                variable_energy={"P2": 0.6},
            ),
            Machine(
                machine_id="M1",
                capacity_rate=100.0,
                min_load_rate=20.0,
                fixed_power=5.0,
                initial_state=0,
                compatible_processes=["P1"],
                variable_energy={"P1": 0.5},
            ),
        ]
        time_horizon = TimeHorizon(
            num_periods=2,
            delta_t=1.0,
            tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
        )
        economics = Economics(
            energy_tariffs=EnergyTariffs(c_peak=30.0, c_offpeak=10.0, c_shoulder=20.0),
            demand_charge_rate=500.0,
            fixed_charge=1000.0,
            purchase_costs={"RAW_A": 50.0, "RAW_Z": 60.0},
            setup_costs={"M1": 500.0, "M2": 700.0},
            holding_costs={"RAW_A": 2.0, "RAW_Z": 3.0},
            penalty_costs={"RAW_A": 100.0, "RAW_Z": 120.0},
        )
        electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        demand = [DemandOrder(resource_id="RAW_A", period=2, quantity=50.0)]

        return FactoryConfiguration(
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

    def test_identical_normalization(self):
        f1 = self._make_factory()
        f2 = self._make_factory()

        norm1 = normalize_factory(f1)
        norm2 = normalize_factory(f2)

        self.assertEqual(norm1.indexes.R, norm2.indexes.R)
        self.assertEqual(norm1.indexes.P, norm2.indexes.P)
        self.assertEqual(norm1.indexes.M, norm2.indexes.M)
        self.assertEqual(norm1.indexes.T, norm2.indexes.T)
        self.assertEqual(norm1.tariff_schedule.energy_rates, norm2.tariff_schedule.energy_rates)
        self.assertEqual(norm1, norm2)

    def test_semantic_preservation(self):
        factory = self._make_factory()
        norm = normalize_factory(factory)

        # Assert no silent scalar modifications
        self.assertEqual(norm.electrical.power_factor, 0.80)
        self.assertEqual(norm.electrical.contract_limit_kva, 100.0)
        self.assertEqual(norm.economics.fixed_charge, 1000.0)
        self.assertEqual(norm.economics.demand_charge_rate, 500.0)
        self.assertEqual(norm.time_horizon.delta_t, 1.0)
        self.assertEqual(norm.time_horizon.num_periods, 2)


if __name__ == "__main__":
    unittest.main()
