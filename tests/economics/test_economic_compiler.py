import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for EconomicCompiler: Tests 1-12, 16, and Golden Micro-Factory."""

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
from industrial_oracle.economics.compiler import EconomicCompiler


class TestEconomicCompiler(unittest.TestCase):
    """M3.0.1 Economic compiler component tests."""

    def _build_factory(self, allow_shortfall: bool = False, fixed_power: float = 4.0, zero_costs: bool = False):
        resources = [
            Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=True),
            Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        ]
        processes = [
            Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.90})
        ]
        machines = [
            Machine(machine_id="M", capacity_rate=50.0, min_load_rate=0.0, fixed_power=fixed_power, initial_state=0, compatible_processes=["P"], variable_energy={"P": 0.5})
        ]
        time_horizon = TimeHorizon(
            num_periods=2,
            delta_t=1.0,
            tariff_partition=TariffPartition(peak_periods=[1], offpeak_periods=[2], shoulder_periods=[]),
        )
        if zero_costs:
            economics = Economics(
                energy_tariffs=EnergyTariffs(c_peak=0.0, c_offpeak=0.0, c_shoulder=0.0),
                demand_charge_rate=0.0,
                fixed_charge=0.0,
                purchase_costs={},
                setup_costs={},
                holding_costs={},
                penalty_costs={},
            )
        else:
            economics = Economics(
                energy_tariffs=EnergyTariffs(c_peak=20.0, c_offpeak=10.0, c_shoulder=0.0),
                demand_charge_rate=500.0,
                fixed_charge=1500.0,
                purchase_costs={"RAW": 80.0},
                setup_costs={"M": 300.0},
                holding_costs={"RAW": 2.0, "FIN": 4.0},
                penalty_costs={"FIN": 250.0},
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

    def test_1_variable_energy_coefficients(self):
        """TEST 1: c[x(m,p,t)] = pi_t * e_var(m,p)."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_x1 = reg.get_index("x", ("M", "P", 1))
        j_x2 = reg.get_index("x", ("M", "P", 2))

        # Period 1: 20 KSh/kWh * 0.5 kWh/kg = 10 KSh/kg
        self.assertEqual(obj.c[j_x1], 20.0 * 0.5)
        # Period 2: 10 KSh/kWh * 0.5 kWh/kg = 5 KSh/kg
        self.assertEqual(obj.c[j_x2], 10.0 * 0.5)

    def test_2_fixed_power_coefficients(self):
        """TEST 2: c[z(m,t)] = pi_t * e_fixed(m) * delta_t."""
        factory = self._build_factory(fixed_power=4.0)
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_z1 = reg.get_index("z", ("M", 1))
        j_z2 = reg.get_index("z", ("M", 2))

        # Period 1: 20 KSh/kWh * 4.0 kW * 1.0 h = 80 KSh
        self.assertEqual(obj.c[j_z1], 20.0 * 4.0 * 1.0)
        # Period 2: 10 KSh/kWh * 4.0 kW * 1.0 h = 40 KSh
        self.assertEqual(obj.c[j_z2], 10.0 * 4.0 * 1.0)

    def test_3_demand_coefficient(self):
        """TEST 3: c[PeakKVA] = lambda_D."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_peak = reg.get_index("PeakKVA", ())
        self.assertEqual(obj.c[j_peak], 500.0)

    def test_4_purchase_coefficients(self):
        """TEST 4: c[Receipts(r,t)] = q_r."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_rec1 = reg.get_index("Receipts", ("RAW", 1))
        j_rec2 = reg.get_index("Receipts", ("RAW", 2))
        self.assertEqual(obj.c[j_rec1], 80.0)
        self.assertEqual(obj.c[j_rec2], 80.0)

    def test_5_startup_coefficients(self):
        """TEST 5: c[Startup(m,t)] = s_m."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_s1 = reg.get_index("Startup", ("M", 1))
        j_s2 = reg.get_index("Startup", ("M", 2))
        self.assertEqual(obj.c[j_s1], 300.0)
        self.assertEqual(obj.c[j_s2], 300.0)

    def test_6_holding_coefficients(self):
        """TEST 6: c[Inv(r,t)] = h_r."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_inv_raw1 = reg.get_index("Inv", ("RAW", 1))
        j_inv_fin1 = reg.get_index("Inv", ("FIN", 1))
        self.assertEqual(obj.c[j_inv_raw1], 2.0)
        self.assertEqual(obj.c[j_inv_fin1], 4.0)

    def test_7_and_10_shortfall_coefficients_soft_demand(self):
        """TEST 7 & 10: Soft demand compiles c[Short(r,t)] = p_r."""
        factory = self._build_factory(allow_shortfall=True)
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_short1 = reg.get_index("Short", ("FIN", 1))
        j_short2 = reg.get_index("Short", ("FIN", 2))
        self.assertEqual(obj.c[j_short1], 250.0)
        self.assertEqual(obj.c[j_short2], 250.0)

    def test_8_fixed_charge_scalar(self):
        """TEST 8: FixedCharge = F and F does not appear in c."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        self.assertEqual(obj.fixed_charge, 1500.0)
        # Verify F is not added into any c_j
        for j in range(len(reg)):
            rec = reg.get_record(j)
            if rec.symbol not in ("x", "z", "Startup", "Inv", "Receipts", "Short", "PeakKVA"):
                self.assertEqual(obj.c[j], 0.0)

    def test_9_hard_demand_no_short_variables(self):
        """TEST 9: In hard mode, Short variables do not exist."""
        factory = self._build_factory(allow_shortfall=False)
        reg = build_variable_registry(factory)

        with self.assertRaises(KeyError):
            reg.get_index("Short", ("FIN", 1))

    def test_11_zero_economic_coefficients(self):
        """TEST 11: Zero cost components produce zero c_j without indexing distortion."""
        factory = self._build_factory(zero_costs=True)
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        self.assertEqual(sum(obj.c), 0.0)
        self.assertEqual(obj.fixed_charge, 0.0)
        self.assertEqual(len(obj.c), len(reg))

    def test_12_factory_x_economic_compilation(self):
        """TEST 12: Multi-machine multi-process Factory-X economic compilation."""
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
        factory = normalize_factory(factory_raw)
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        self.assertEqual(len(obj.c), 265)
        self.assertEqual(obj.fixed_charge, 1000.0)

        # Check peak tariff period (t=9) vs offpeak (t=1)
        j_m1_p1_t9 = reg.get_index("x", ("M1", "P1", 9))
        j_m1_p1_t1 = reg.get_index("x", ("M1", "P1", 1))
        self.assertEqual(obj.c[j_m1_p1_t9], 30.0 * 0.5)
        self.assertEqual(obj.c[j_m1_p1_t1], 10.0 * 0.5)

    def test_16_traceability(self):
        """TEST 16: Every nonzero coefficient maps back to its provenance."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        for col, val in enumerate(obj.c):
            if val != 0.0:
                self.assertIn(col, obj.provenance)
                entries = obj.provenance[col]
                self.assertTrue(len(entries) >= 1)
                self.assertTrue(entries[0].formula != "")
                self.assertTrue(entries[0].unit != "")

    def test_golden_micro_factory_objective(self):
        """Section 20 & 21: Exact golden benchmark objective Z = 10 x1 + 5 x2 + 500 PeakKVA."""
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
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        j_x1 = reg.get_index("x", ("M", "P", 1))
        j_x2 = reg.get_index("x", ("M", "P", 2))
        j_peak = reg.get_index("PeakKVA", ())

        self.assertEqual(len(obj.c), 13)
        self.assertEqual(obj.c[j_x1], 10.0)
        self.assertEqual(obj.c[j_x2], 5.0)
        self.assertEqual(obj.c[j_peak], 500.0)
        self.assertEqual(obj.fixed_charge, 0.0)

        # All other coefficients zero
        for j in range(13):
            if j not in (j_x1, j_x2, j_peak):
                self.assertEqual(obj.c[j], 0.0)


if __name__ == "__main__":
    unittest.main()
