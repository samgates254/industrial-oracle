import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Process domain entity."""

import unittest
from pydantic import ValidationError
from industrial_oracle.domain.processes import Process


class TestProcessDomain(unittest.TestCase):
    """Process domain representation tests."""

    def test_create_transformation_process(self):
        """Test 2: Create P1: RAW -> 0.90 INTERMEDIATE."""
        proc = Process(
            process_id="P1",
            input_coefficients={"RAW": 1.0},
            output_coefficients={"INTERMEDIATE": 0.90},
        )
        self.assertEqual(proc.process_id, "P1")
        self.assertEqual(proc.input_coefficients["RAW"], 1.0)
        self.assertEqual(proc.output_coefficients["INTERMEDIATE"], 0.90)

    def test_process_immutability(self):
        """Test that Process instance is frozen."""
        proc = Process(
            process_id="P1",
            input_coefficients={"RAW": 1.0},
            output_coefficients={"INTERMEDIATE": 0.90},
        )
        with self.assertRaises((TypeError, ValidationError)):
            proc.process_id = "P2"


if __name__ == "__main__":
    unittest.main()
