import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Process validation."""

import unittest
from industrial_oracle.domain.processes import Process
from industrial_oracle.validation.exceptions import PhysicalValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_process


class TestProcessValidation(unittest.TestCase):
    """Unit tests for Process validation."""

    def test_valid_multi_input_multi_output(self):
        proc = Process(
            process_id="P_MULTI",
            input_coefficients={"R1": 1.0, "R2": 0.5},
            output_coefficients={"WIP1": 0.8, "WIP2": 0.2},
        )
        validate_process(proc)

    def test_negative_input_coefficient(self):
        proc = Process(
            process_id="P1",
            input_coefficients={"RAW": -1.0},
            output_coefficients={"INTERMEDIATE": 0.9},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_process(proc)

    def test_negative_output_coefficient(self):
        proc = Process(
            process_id="P1",
            input_coefficients={"RAW": 1.0},
            output_coefficients={"INTERMEDIATE": -0.9},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_process(proc)

    def test_both_mappings_empty(self):
        proc = Process(
            process_id="P_EMPTY",
            input_coefficients={},
            output_coefficients={},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_process(proc)

    def test_empty_process_id(self):
        proc = Process(
            process_id="",
            input_coefficients={"RAW": 1.0},
            output_coefficients={"INTERMEDIATE": 0.9},
        )
        with self.assertRaises(SchemaValidationError):
            validate_process(proc)


if __name__ == "__main__":
    unittest.main()
