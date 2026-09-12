import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for VariableRegistry, bijection, and variable-count formula."""

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
from industrial_oracle.model.variables import build_variable_registry


class TestVariableRegistry(unittest.TestCase):
    """Variable registry verification tests."""

    def _make_factory(self, allow_shortfall: bool = False, raw_purchasable: bool = False):
        resources = [
            Resource(
                resource_id="RAW",
                category=ResourceCategory.RAW,
                initial_stock=100.0,
                safety_stock=0.0,
                max_storage=1000.0,
                is_purchasable=raw_purchasable,
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
            configuration_policy=ConfigurationPolicy(allow_demand_shortfall=allow_shortfall),
            time_horizon=time_horizon,
            resources=resources,
            processes=processes,
            machines=machines,
            economics=economics,
            electrical_parameters=electrical,
            demand=demand,
        )
        return normalize_factory(factory_raw)

    def test_variable_count_formula_hard_non_purchasable(self):
        """Micro-Factory baseline: RAW non-purchasable, hard demand -> exactly 13 variables."""
        factory = self._make_factory(allow_shortfall=False, raw_purchasable=False)
        reg = build_variable_registry(factory)

        N_T = factory.time_horizon.num_periods
        K = factory.indexes.num_compatible_pairs
        M_count = factory.indexes.num_machines
        R_count = factory.indexes.num_resources
        R_purch = len([r for r in factory.resources if r.is_purchasable])
        R_fin = len([r for r in factory.resources if r.category == "FINISHED"])
        is_soft = factory.configuration_policy.allow_demand_shortfall

        formula_count = N_T * (K + 2 * M_count + R_count + R_purch + R_fin + (R_fin if is_soft else 0)) + 1
        self.assertEqual(formula_count, 13)
        self.assertEqual(len(reg), 13)

    def test_variable_count_formula_purchasable(self):
        """With RAW purchasable -> N_vars = 15."""
        factory = self._make_factory(allow_shortfall=False, raw_purchasable=True)
        reg = build_variable_registry(factory)

        N_T = factory.time_horizon.num_periods
        K = factory.indexes.num_compatible_pairs
        M_count = factory.indexes.num_machines
        R_count = factory.indexes.num_resources
        R_purch = len([r for r in factory.resources if r.is_purchasable])
        R_fin = len([r for r in factory.resources if r.category == "FINISHED"])
        is_soft = factory.configuration_policy.allow_demand_shortfall

        formula_count = N_T * (K + 2 * M_count + R_count + R_purch + R_fin + (R_fin if is_soft else 0)) + 1
        self.assertEqual(formula_count, 15)
        self.assertEqual(len(reg), 15)

    def test_variable_count_formula_soft_mode(self):
        """With soft demand enabled -> N_vars increases by R_fin * N_T."""
        factory = self._make_factory(allow_shortfall=True, raw_purchasable=False)
        reg = build_variable_registry(factory)
        self.assertEqual(len(reg), 15)  # 13 + 2(Short) = 15

    def test_column_bijection(self):
        """Verify that column mapping is strictly bijective."""
        factory = self._make_factory(allow_shortfall=False, raw_purchasable=False)
        reg = build_variable_registry(factory)

        seen_indices = set()
        for rec in reg.records:
            self.assertEqual(reg.get_index(rec.symbol, rec.indices), rec.column_index)
            self.assertEqual(reg.get_record(rec.column_index), rec)
            self.assertNotIn(rec.column_index, seen_indices)
            seen_indices.add(rec.column_index)

        self.assertEqual(len(seen_indices), len(reg))

    def test_integer_indices(self):
        """Verify integer indices correspond strictly to z and Startup."""
        factory = self._make_factory(allow_shortfall=False, raw_purchasable=False)
        reg = build_variable_registry(factory)

        for col in reg.integer_indices:
            rec = reg.get_record(col)
            self.assertIn(rec.symbol, ("z", "Startup"))
            self.assertTrue(rec.is_integer)


if __name__ == "__main__":
    unittest.main()
