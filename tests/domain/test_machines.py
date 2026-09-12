import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Machine domain entity."""

import unittest
from pydantic import ValidationError
from industrial_oracle.domain.machines import Machine


class TestMachineDomain(unittest.TestCase):
    """Machine domain representation tests."""

    def test_create_production_machine(self):
        """Test 3: Create M1 machine specifications."""
        m1 = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=20.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        self.assertEqual(m1.machine_id, "M1")
        self.assertEqual(m1.capacity_rate, 100.0)
        self.assertEqual(m1.min_load_rate, 20.0)
        self.assertEqual(m1.fixed_power, 5.0)
        self.assertEqual(m1.initial_state, 0)
        self.assertEqual(m1.compatible_processes, ["P1"])
        self.assertEqual(m1.variable_energy["P1"], 0.5)

    def test_binary_initial_state_validation(self):
        """Test that initial_state rejects non-binary values."""
        with self.assertRaises(ValidationError):
            Machine(
                machine_id="M1",
                capacity_rate=100.0,
                min_load_rate=20.0,
                fixed_power=5.0,
                initial_state=2,
                compatible_processes=["P1"],
                variable_energy={"P1": 0.5},
            )


if __name__ == "__main__":
    unittest.main()
