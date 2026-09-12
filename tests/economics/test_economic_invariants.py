import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for M3 invariants: Determinism, Economic/Physical Separation, Dimensions, Immutability."""

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
from industrial_oracle.model.variables import build_variable_registry
from industrial_oracle.economics.compiler import EconomicCompiler


class TestEconomicInvariants(unittest.TestCase):
    """Verification of M3 mathematical invariants."""

    def _make_factory(self, c_peak: float = 20.0):
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
            energy_tariffs=EnergyTariffs(c_peak=c_peak, c_offpeak=10.0, c_shoulder=0.0),
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
        return normalize_factory(factory_raw)

    def test_13_determinism(self):
        """TEST 13: Compile(I) == Compile(I)."""
        f1 = self._make_factory(c_peak=25.0)
        f2 = self._make_factory(c_peak=25.0)
        reg = build_variable_registry(f1)

        obj1 = EconomicCompiler.compile(f1, reg)
        obj2 = EconomicCompiler.compile(f2, reg)

        self.assertEqual(obj1.c, obj2.c)
        self.assertEqual(obj1.fixed_charge, obj2.fixed_charge)
        self.assertEqual(len(obj1.provenance), len(obj2.provenance))

    def test_14_economic_physical_separation(self):
        """TEST 14: Changing economics alters c, but leaves A_eq, A_ub, l, u, integer_indices unchanged."""
        f_base = self._make_factory(c_peak=20.0)
        f_alt = self._make_factory(c_peak=35.0)

        m_base = ModelCompiler.compile(f_base)
        m_alt = ModelCompiler.compile(f_alt)

        # Physical constraints MUST remain identical
        self.assertEqual(m_base.A_eq_dense, m_alt.A_eq_dense)
        self.assertEqual(m_base.b_eq, m_alt.b_eq)
        self.assertEqual(m_base.A_ub_dense, m_alt.A_ub_dense)
        self.assertEqual(m_base.b_ub, m_alt.b_ub)
        self.assertEqual(m_base.l, m_alt.l)
        self.assertEqual(m_base.u, m_alt.u)
        self.assertEqual(m_base.integer_indices, m_alt.integer_indices)

        # But c differs exactly on x1: 20 * 0.5 = 10.0 vs 35 * 0.5 = 17.5
        j_x1 = m_base.variable_registry.get_index("x", ("M", "P", 1))
        self.assertEqual(m_base.c[j_x1], 10.0)
        self.assertEqual(m_alt.c[j_x1], 17.5)

    def test_15_dimensional_correctness(self):
        """TEST 15: Dimensional evaluation matches [KSh]."""
        factory = self._make_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        for col, prov_list in obj.provenance.items():
            rec = reg.get_record(col)
            for p in prov_list:
                if p.component == "ENERGY_VARIABLE":
                    # [KSh/kWh] * [kWh/kg] * [kg] = [KSh]
                    self.assertEqual(p.unit, "KSh/kg")
                    self.assertEqual(rec.unit, "kg")
                elif p.component == "DEMAND_CHARGE":
                    # [KSh/kVA] * [kVA] = [KSh]
                    self.assertEqual(p.unit, "KSh/kVA")
                    self.assertEqual(rec.unit, "kVA")

    def test_immutability(self):
        """EconomicObjective cannot be mutated after construction."""
        factory = self._make_factory()
        reg = build_variable_registry(factory)
        obj = EconomicCompiler.compile(factory, reg)

        with self.assertRaises(Exception):
            obj.fixed_charge = 999.0

        with self.assertRaises(TypeError):
            obj.provenance[0] = ()


if __name__ == "__main__":
    unittest.main()
