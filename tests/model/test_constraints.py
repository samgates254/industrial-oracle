import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for constraint compilation, row counts, and physical edge conditions."""

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
from industrial_oracle.model.constraints import compile_constraints
from industrial_oracle.model.variables import build_variable_registry


class TestConstraintCompilation(unittest.TestCase):
    """Constraint row generation tests."""

    def _build_factory(self, allow_shortfall: bool = False, initial_state: int = 0, fixed_power: float = 0.0, min_load: float = 0.0):
        resources = [
            Resource(resource_id="RAW", category=ResourceCategory.RAW, initial_stock=100.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
            Resource(resource_id="FIN", category=ResourceCategory.FINISHED, initial_stock=0.0, safety_stock=0.0, max_storage=1000.0, is_purchasable=False),
        ]
        processes = [
            Process(process_id="P", input_coefficients={"RAW": 1.0}, output_coefficients={"FIN": 0.90})
        ]
        machines = [
            Machine(machine_id="M", capacity_rate=50.0, min_load_rate=min_load, fixed_power=fixed_power, initial_state=initial_state, compatible_processes=["P"], variable_energy={"P": 0.5})
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

    def test_row_count_audit(self):
        """Verify theoretical row count formulas."""
        factory = self._build_factory()
        reg = build_variable_registry(factory)
        eq_rows, ub_rows = compile_constraints(factory, reg)

        N_T = factory.time_horizon.num_periods
        R_count = factory.indexes.num_resources
        R_fin = len([r for r in factory.resources if r.category == "FINISHED"])
        M_count = factory.indexes.num_machines

        expected_eq = R_count * N_T + R_fin * N_T
        self.assertEqual(len(eq_rows), expected_eq)
        self.assertEqual(len(eq_rows), 6)

        expected_ub = (5 * M_count + 1) * N_T
        self.assertEqual(len(ub_rows), expected_ub)
        self.assertEqual(len(ub_rows), 12)

    def test_hard_demand_zero_semantics(self):
        """Correction 4 & Dimension 9: Ship=0 when demand=0; Ship=Demand when demand>0."""
        factory = self._build_factory(allow_shortfall=False)
        reg = build_variable_registry(factory)
        eq_rows, _ = compile_constraints(factory, reg)

        dmd_t1 = [r for r in eq_rows if r.equation_id == "EQ-DMD-001_FIN_1"][0]
        dmd_t2 = [r for r in eq_rows if r.equation_id == "EQ-DMD-001_FIN_2"][0]

        self.assertEqual(dmd_t1.rhs, 0.0)
        self.assertEqual(dmd_t2.rhs, 36.0)

    def test_soft_demand_equation(self):
        """Dimension 8: Ship + Short = Demand in soft mode."""
        factory = self._build_factory(allow_shortfall=True)
        reg = build_variable_registry(factory)
        eq_rows, _ = compile_constraints(factory, reg)

        dmd_t2 = [r for r in eq_rows if r.equation_id == "EQ-DMD-001_FIN_2"][0]
        j_ship = reg.get_index("Ship", ("FIN", 2))
        j_short = reg.get_index("Short", ("FIN", 2))

        self.assertEqual(dmd_t2.coefficients[j_ship], 1.0)
        self.assertEqual(dmd_t2.coefficients[j_short], 1.0)
        self.assertEqual(dmd_t2.rhs, 36.0)

    def test_startup_triad_z0_zero(self):
        """Dimension 7A: Startup transitions for z0 = 0."""
        factory = self._build_factory(initial_state=0)
        reg = build_variable_registry(factory)
        _, ub_rows = compile_constraints(factory, reg)

        s1 = [r for r in ub_rows if r.equation_id == "EQ-STR-001_M_1"][0]
        s3 = [r for r in ub_rows if r.equation_id == "EQ-STR-003_M_1"][0]

        # s1: -Startup_1 + z_1 <= z0 = 0.0
        self.assertEqual(s1.rhs, 0.0)
        # s3: Startup_1 <= 1 - z0 = 1.0
        self.assertEqual(s3.rhs, 1.0)

    def test_startup_triad_z0_one(self):
        """Dimension 7B: Startup transitions for z0 = 1."""
        factory = self._build_factory(initial_state=1)
        reg = build_variable_registry(factory)
        _, ub_rows = compile_constraints(factory, reg)

        s1 = [r for r in ub_rows if r.equation_id == "EQ-STR-001_M_1"][0]
        s3 = [r for r in ub_rows if r.equation_id == "EQ-STR-003_M_1"][0]

        # s1: -Startup_1 + z_1 <= z0 = 1.0
        self.assertEqual(s1.rhs, 1.0)
        # s3: Startup_1 <= 1 - z0 = 0.0 (forces Startup_1 <= 0 since machine already running)
        self.assertEqual(s3.rhs, 0.0)

    def test_minimum_load_coefficients(self):
        """Dimension 6: Minimum-load coefficients in EQ-MIN-001."""
        factory = self._build_factory(min_load=15.0)
        reg = build_variable_registry(factory)
        _, ub_rows = compile_constraints(factory, reg)

        min_row = [r for r in ub_rows if r.equation_id == "EQ-MIN-001_M_1"][0]
        j_x = reg.get_index("x", ("M", "P", 1))
        j_z = reg.get_index("z", ("M", 1))

        # -x + MinLoad * delta_t * z <= 0
        self.assertEqual(min_row.coefficients[j_x], -1.0)
        self.assertEqual(min_row.coefficients[j_z], 15.0)

    def test_fixed_power_in_peak_kva(self):
        """Dimension 10: Fixed power contribution (e_fixed / cos_phi) to peak kVA."""
        factory = self._build_factory(fixed_power=4.0)
        reg = build_variable_registry(factory)
        _, ub_rows = compile_constraints(factory, reg)

        peak_row = [r for r in ub_rows if r.equation_id == "EQ-PEAK-001_1"][0]
        j_z = reg.get_index("z", ("M", 1))

        # e_fixed / cos_phi = 4.0 / 0.8 = 5.0
        self.assertEqual(peak_row.coefficients[j_z], 5.0)


if __name__ == "__main__":
    unittest.main()
