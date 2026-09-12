import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Regression tests for M1.3.1 audit fixes:
1. True read-only immutability of normalized mappings.
2. Cross-reference canonicalization with surrounding whitespace.
"""

import unittest
from dataclasses import FrozenInstanceError
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


class TestM131AuditFixes(unittest.TestCase):
    """M1.3.1 regression tests."""

    def _build_factory_with_whitespace(self):
        resources = [
            Resource(
                resource_id="  RAW  ",
                category=ResourceCategory.RAW,
                initial_stock=100.0,
                safety_stock=10.0,
                max_storage=500.0,
                is_purchasable=True,
            ),
            Resource(
                resource_id="  FINISHED  ",
                category=ResourceCategory.FINISHED,
                initial_stock=0.0,
                safety_stock=0.0,
                max_storage=500.0,
                is_purchasable=False,
            ),
        ]
        processes = [
            Process(
                process_id="  P1  ",
                input_coefficients={"  RAW  ": 1.0},
                output_coefficients={"  FINISHED  ": 0.90},
            )
        ]
        machines = [
            Machine(
                machine_id="  M1  ",
                capacity_rate=100.0,
                min_load_rate=10.0,
                fixed_power=5.0,
                initial_state=0,
                compatible_processes=["  P1  "],
                variable_energy={"  P1  ": 0.5},
            )
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
            purchase_costs={"  RAW  ": 80.0},
            setup_costs={"  M1  ": 500.0},
            holding_costs={"  RAW  ": 2.0, "  FINISHED  ": 4.0},
            penalty_costs={"  FINISHED  ": 200.0},
        )
        electrical = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        demand = [DemandOrder(resource_id="  FINISHED  ", period=2, quantity=150.0)]

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

    def test_true_readonly_mappings(self):
        """Issue 1 Acceptance Test: Attempted mapping mutations raise TypeError."""
        factory = self._build_factory_with_whitespace()
        norm = normalize_factory(factory)

        # 1. NormalizedDemand.demand_by_resource_period
        with self.assertRaises(TypeError):
            norm.demand.demand_by_resource_period[("FINISHED", 2)] = 999.0

        # 2. CanonicalIndexSets.M_p and P_m
        with self.assertRaises(TypeError):
            norm.indexes.M_p["P1"] = ("M2",)

        with self.assertRaises(TypeError):
            norm.indexes.P_m["M1"] = ("P2",)

        # 3. NormalizedMachine.variable_energy_kwh_per_kg
        with self.assertRaises(TypeError):
            norm.machines[0].variable_energy_kwh_per_kg["P1"] = 99.0

        # 4. NormalizedProcess.input_coefficients & output_coefficients
        with self.assertRaises(TypeError):
            norm.processes[0].input_coefficients["RAW"] = 99.0

        with self.assertRaises(TypeError):
            norm.processes[0].output_coefficients["FINISHED"] = 99.0

        # 5. Tariff schedule mappings
        with self.assertRaises(TypeError):
            norm.tariff_schedule.energy_rates[1] = 99.0

        # 6. Economics mappings
        with self.assertRaises(TypeError):
            norm.economics.purchase_costs["RAW"] = 99.0

        # 7. Frozen dataclass field reassignment prohibited
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            norm.economics = None

    def test_cross_reference_canonicalization(self):
        """Issue 2 Acceptance Test: Whitespace in identifiers is canonicalized and relations hold."""
        factory = self._build_factory_with_whitespace()
        norm = normalize_factory(factory)

        # All entity IDs resolved without whitespace
        self.assertEqual(norm.indexes.R, ("FINISHED", "RAW"))
        self.assertEqual(norm.indexes.P, ("P1",))
        self.assertEqual(norm.indexes.M, ("M1",))

        # Compatibility invariant: p in P_m <=> m in M_p
        self.assertEqual(norm.indexes.P_m["M1"], ("P1",))
        self.assertEqual(norm.indexes.M_p["P1"], ("M1",))
        self.assertIn("P1", norm.indexes.P_m["M1"])
        self.assertIn("M1", norm.indexes.M_p["P1"])

        # Machine and Process internal references resolved
        self.assertEqual(norm.machines[0].compatible_processes, ("P1",))
        self.assertIn("P1", norm.machines[0].variable_energy_kwh_per_kg)
        self.assertIn("RAW", norm.processes[0].input_coefficients)
        self.assertIn("FINISHED", norm.processes[0].output_coefficients)

        # Demand resource reference resolved
        self.assertEqual(norm.demand.demand_by_resource_period[("FINISHED", 2)], 150.0)


if __name__ == "__main__":
    unittest.main()
