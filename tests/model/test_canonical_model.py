import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for end-to-end CanonicalModel compilation, golden audit, and immutability."""

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


class TestCanonicalModel(unittest.TestCase):
    """Canonical model end-to-end audit."""

    def _build_golden_factory(self):
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
        return normalize_factory(factory_raw)

    def test_golden_matrix_audit(self):
        """Micro-Factory Golden Reference matrix structure audit."""
        factory = self._build_golden_factory()
        model = ModelCompiler.compile(factory)

        # 1. Variable Count: exactly 13 columns
        self.assertEqual(model.num_variables, 13)

        # 2. Objective coefficients
        j_x1 = model.variable_registry.get_index("x", ("M", "P", 1))
        j_x2 = model.variable_registry.get_index("x", ("M", "P", 2))
        j_peak = model.variable_registry.get_index("PeakKVA", ())

        self.assertEqual(model.c[j_x1], 10.0)   # 20.0 * 0.5 = 10.0
        self.assertEqual(model.c[j_x2], 5.0)    # 10.0 * 0.5 = 5.0
        self.assertEqual(model.c[j_peak], 500.0)

        # 3. Peak inequality rows
        peak_row_t1 = [r for r in model.A_ub_sparse if r.equation_id == "EQ-PEAK-001_1"][0]
        peak_row_t2 = [r for r in model.A_ub_sparse if r.equation_id == "EQ-PEAK-001_2"][0]

        # e / (delta_t * cos_phi) = 0.5 / (1.0 * 0.8) = 0.625
        self.assertAlmostEqual(peak_row_t1.coefficients[j_x1], 0.625)
        self.assertAlmostEqual(peak_row_t1.coefficients[j_peak], -1.0)
        self.assertAlmostEqual(peak_row_t2.coefficients[j_x2], 0.625)
        self.assertAlmostEqual(peak_row_t2.coefficients[j_peak], -1.0)

        # 4. Equality rows
        dmd_row = [r for r in model.A_eq_sparse if r.equation_id == "EQ-DMD-001_FIN_2"][0]
        self.assertEqual(dmd_row.rhs, 36.0)

        bal_row = [r for r in model.A_eq_sparse if r.equation_id == "EQ-BAL-001A_RAW_1"][0]
        # Inv_{RAW,1} - (-1.0) x_1 = 100.0 => Inv + x = 100
        j_inv_raw1 = model.variable_registry.get_index("Inv", ("RAW", 1))
        self.assertEqual(bal_row.coefficients[j_inv_raw1], 1.0)
        self.assertEqual(bal_row.coefficients[j_x1], 1.0)
        self.assertEqual(bal_row.rhs, 100.0)

    def test_recursive_canonical_model_immutability(self):
        """CanonicalModel and all internal mappings must be strictly read-only."""
        factory = self._build_golden_factory()
        model = ModelCompiler.compile(factory)

        # 1. Attribute reassignment on CanonicalModel
        with self.assertRaises(Exception):
            model.fixed_charge = 100.0

        # 2. Mutation on SparseRow mapping
        with self.assertRaises(TypeError):
            model.A_ub_sparse[0].coefficients[0] = 999.0

        # 3. Mutation on row mappings
        with self.assertRaises(TypeError):
            model.eq_row_to_id[0] = "MUTATED"

        with self.assertRaises(TypeError):
            model.ub_row_to_id[0] = "MUTATED"

    def test_sparse_dense_equivalence(self):
        """Dimension 16: Verify sparse rows match dense matrix rows identically."""
        factory = self._build_golden_factory()
        model = ModelCompiler.compile(factory)

        # Equality rows
        for idx, sparse_row in enumerate(model.A_eq_sparse):
            dense_row = model.A_eq_dense[idx]
            self.assertEqual(sparse_row.to_dense(model.num_variables), dense_row)
            for col, val in sparse_row.coefficients.items():
                self.assertEqual(dense_row[col], val)

        # Inequality rows
        for idx, sparse_row in enumerate(model.A_ub_sparse):
            dense_row = model.A_ub_dense[idx]
            self.assertEqual(sparse_row.to_dense(model.num_variables), dense_row)
            for col, val in sparse_row.coefficients.items():
                self.assertEqual(dense_row[col], val)

    def test_deterministic_compilation(self):
        """Dimension 17: Compile(I) == Compile(I)."""
        f1 = self._build_golden_factory()
        f2 = self._build_golden_factory()

        m1 = ModelCompiler.compile(f1)
        m2 = ModelCompiler.compile(f2)

        self.assertEqual(m1.c, m2.c)
        self.assertEqual(m1.fixed_charge, m2.fixed_charge)
        self.assertEqual(m1.b_eq, m2.b_eq)
        self.assertEqual(m1.b_ub, m2.b_ub)
        self.assertEqual(m1.l, m2.l)
        self.assertEqual(m1.u, m2.u)
        self.assertEqual(m1.integer_indices, m2.integer_indices)
        self.assertEqual(m1.eq_row_ids, m2.eq_row_ids)
        self.assertEqual(m1.ub_row_ids, m2.ub_row_ids)

    def test_complete_row_id_bijection(self):
        """Dimension 18: Complete bijective mapping between row indices and IDs."""
        factory = self._build_golden_factory()
        model = ModelCompiler.compile(factory)

        # Equality row bijection
        self.assertEqual(len(model.eq_row_to_id), model.num_equalities)
        self.assertEqual(len(model.eq_id_to_row), model.num_equalities)
        for idx, eq_id in model.eq_row_to_id.items():
            self.assertEqual(model.eq_id_to_row[eq_id], idx)

        # Inequality row bijection
        self.assertEqual(len(model.ub_row_to_id), model.num_inequalities)
        self.assertEqual(len(model.ub_id_to_row), model.num_inequalities)
        for idx, ub_id in model.ub_row_to_id.items():
            self.assertEqual(model.ub_id_to_row[ub_id], idx)



    def test_empty_a_eq_preservation(self):
        """Regression test: Ensure empty A_eq matrix is preserved as empty tuple, not substituted by A_ub."""
        from industrial_oracle.model.compiler import CanonicalModel, ModelCompiler
        from types import MappingProxyType

        factory = self._build_golden_factory()
        model = ModelCompiler.compile(factory)

        # Construct a synthetic canonical model with 0 equality rows
        synthetic_model = CanonicalModel(
            c=model.c,
            fixed_charge=model.fixed_charge,
            A_ub_sparse=model.A_ub_sparse,
            A_ub_dense=model.A_ub_dense,
            b_ub=model.b_ub,
            A_eq_sparse=(),
            A_eq_dense=(),
            b_eq=(),
            l=model.l,
            u=model.u,
            integer_indices=model.integer_indices,
            variable_registry=model.variable_registry,
            eq_row_ids=(),
            ub_row_ids=model.ub_row_ids,
            eq_row_to_id=MappingProxyType({}),
            eq_id_to_row=MappingProxyType({}),
            ub_row_to_id=model.ub_row_to_id,
            ub_id_to_row=model.ub_id_to_row,
        )

        self.assertEqual(synthetic_model.A_eq_dense, ())
        self.assertEqual(synthetic_model.num_equalities, 0)
        self.assertNotEqual(synthetic_model.A_eq_dense, synthetic_model.A_ub_dense)


if __name__ == "__main__":
    unittest.main()
