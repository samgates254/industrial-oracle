import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for JSON serialization of DiagnosticReport."""

import json
import unittest
from industrial_oracle.normalization.factory import normalize_factory
from industrial_oracle.model.compiler import ModelCompiler
from industrial_oracle.solver.adapters.highs import HiGHSSolver
from industrial_oracle.diagnostics.engine import DiagnosticsEngine
from industrial_oracle.cli.serializers import (
    serialize_diagnostic_report_to_dict,
    serialize_diagnostic_report_to_json,
)
import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)
from tests.verification.fixtures.analytical_truth_sets import make_micro_factory_fixture


class TestSerializers(unittest.TestCase):
    """DiagnosticReport JSON and dictionary serialization tests."""

    def setUp(self):
        self.factory = normalize_factory(make_micro_factory_fixture())
        self.model = ModelCompiler.compile(self.factory)
        self.solver = HiGHSSolver()
        self.result = self.solver.solve(self.model)
        self.report = DiagnosticsEngine.analyze(self.factory, self.model, self.result)

    def test_serialize_to_dict_and_json(self):
        data = serialize_diagnostic_report_to_dict(self.report)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["solver_status"], "OPTIMAL")
        self.assertEqual(data["feasibility"]["is_verified_feasible"], True)

        json_str = serialize_diagnostic_report_to_json(self.report)
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["factory_name"], self.factory.contract_title)
        self.assertEqual(parsed["economics"]["total_cost"], 6550.0)


if __name__ == "__main__":
    unittest.main()
