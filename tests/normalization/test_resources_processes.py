import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for Resource and Process normalization."""

import math
import unittest
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.processes import Process
from industrial_oracle.domain.resources import Resource
from industrial_oracle.normalization.processes import normalize_process
from industrial_oracle.normalization.resources import normalize_resource


class TestResourcesProcessesNormalization(unittest.TestCase):
    """Resource supply-cap and process transformation normalization tests."""

    def test_supply_cap_explicit_vs_none(self):
        res_explicit = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
            supply_cap=[100.0, 200.0],
        )
        norm_explicit = normalize_resource(res_explicit, num_periods=2)
        self.assertEqual(norm_explicit.supply_cap, (100.0, 200.0))

        res_none = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
            supply_cap=None,
        )
        norm_none = normalize_resource(res_none, num_periods=2)
        self.assertEqual(norm_none.supply_cap, (math.inf, math.inf))

    def test_process_deterministic_sorting(self):
        proc = Process(
            process_id="P_SORT",
            input_coefficients={"Z_RAW": 2.0, "A_RAW": 1.0},
            output_coefficients={"Z_WIP": 1.8, "A_WIP": 0.9},
        )
        norm_proc = normalize_process(proc)
        self.assertEqual(list(norm_proc.input_coefficients.keys()), ["A_RAW", "Z_RAW"])
        self.assertEqual(list(norm_proc.output_coefficients.keys()), ["A_WIP", "Z_WIP"])


if __name__ == "__main__":
    unittest.main()
