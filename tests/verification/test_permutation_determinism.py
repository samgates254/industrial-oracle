import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Pillar V: Permutation Invariance and Determinism."""

import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from .fixtures.permutation_cases import make_permuted_factory_pair


class TestPermutationDeterminism(unittest.TestCase):
    """Verification that declaration permutations yield identical canonical models and solutions."""

    def test_permutation_canonical_model_equality(self):
        """Pillar V: Declaring entities in different orders produces identical CanonicalModel matrices."""
        f1_raw, f2_raw = make_permuted_factory_pair()

        f1 = normalize_factory(f1_raw)
        f2 = normalize_factory(f2_raw)

        m1 = ModelCompiler.compile(f1)
        m2 = ModelCompiler.compile(f2)

        # 1. Canonical matrix equality
        self.assertEqual(m1.c, m2.c)
        self.assertEqual(m1.fixed_charge, m2.fixed_charge)
        self.assertEqual(m1.A_eq_dense, m2.A_eq_dense)
        self.assertEqual(m1.b_eq, m2.b_eq)
        self.assertEqual(m1.A_ub_dense, m2.A_ub_dense)
        self.assertEqual(m1.b_ub, m2.b_ub)
        self.assertEqual(m1.l, m2.l)
        self.assertEqual(m1.u, m2.u)
        self.assertEqual(m1.integer_indices, m2.integer_indices)
        self.assertEqual(m1.eq_row_ids, m2.eq_row_ids)
        self.assertEqual(m1.ub_row_ids, m2.ub_row_ids)

        # 2. Solver outcome equality within numerical tolerance
        solver = HiGHSSolver()
        res1 = solver.solve(m1)
        res2 = solver.solve(m2)

        self.assertEqual(res1.status, res2.status)
        self.assertAlmostEqual(res1.objective_value, res2.objective_value, delta=1e-6)
        for y1, y2 in zip(res1.primal_values, res2.primal_values):
            self.assertAlmostEqual(y1, y2, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
