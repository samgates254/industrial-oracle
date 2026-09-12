import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for M0.1 Golden Benchmark Normalization Fixture."""

import math
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


class TestGoldenBenchmarkNormalization(unittest.TestCase):
    """M0.1 Micro-Factory golden reference normalization test."""

    def test_golden_fixture_normalization_preservation(self):
        resources = [
            Resource(
                resource_id="RAW",
                category=ResourceCategory.RAW,
                initial_stock=100.0,
                safety_stock=0.0,
                max_storage=1000.0,
                is_purchasable=False,
            ),
            Resource(
                resource_id="FIN",
                category=ResourceCategory.FINISHED,
                initial_stock=0.0,
                safety_stock=0.0,
                max_storage=1000.0,
                is_purchasable=False,
            ),
        ]
        processes = [
            Process(
                process_id="P",
                input_coefficients={"RAW": 1.0},
                output_coefficients={"FIN": 0.90},
            )
        ]
        machines = [
            Machine(
                machine_id="M",
                capacity_rate=50.0,
                min_load_rate=0.0,
                fixed_power=0.0,
                initial_state=0,
                compatible_processes=["P"],
                variable_energy={"P": 0.5},
            )
        ]
        time_horizon = TimeHorizon(
            num_periods=2,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[],
            ),
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
        electrical = ElectricalParameters(
            power_factor=0.80,
            contract_limit_kva=100.0,
        )
        demand = [
            DemandOrder(resource_id="FIN", period=2, quantity=36.0)
        ]

        golden_factory = FactoryConfiguration(
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

        norm = normalize_factory(golden_factory)

        # Structural Verification
        self.assertEqual(norm.indexes.R, ("FIN", "RAW"))
        self.assertEqual(norm.indexes.P, ("P",))
        self.assertEqual(norm.indexes.M, ("M",))
        self.assertEqual(norm.indexes.T, (1, 2))
        self.assertEqual(norm.indexes.M_p["P"], ("M",))
        self.assertEqual(norm.indexes.P_m["M"], ("P",))

        # Value Preservation
        self.assertEqual(norm.processes[0].input_coefficients["RAW"], 1.0)
        self.assertEqual(norm.processes[0].output_coefficients["FIN"], 0.90)
        self.assertEqual(norm.machines[0].capacity_rate_kg_per_h, 50.0)
        self.assertEqual(norm.machines[0].variable_energy_kwh_per_kg["P"], 0.5)
        self.assertEqual(norm.electrical.power_factor, 0.80)
        self.assertEqual(norm.electrical.contract_limit_kva, 100.0)
        self.assertEqual(norm.tariff_schedule.energy_rates[1], 20.0)
        self.assertEqual(norm.tariff_schedule.energy_rates[2], 10.0)
        self.assertEqual(norm.demand.demand_by_resource_period[("FIN", 2)], 36.0)

        # Preserved Supply Cap (None -> inf)
        self.assertEqual(norm.resources[0].supply_cap, (math.inf, math.inf))
        self.assertEqual(norm.resources[1].supply_cap, (math.inf, math.inf))


if __name__ == "__main__":
    unittest.main()
