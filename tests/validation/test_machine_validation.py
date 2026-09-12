import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Machine validation."""

import unittest
from industrial_oracle.domain.machines import Machine
from industrial_oracle.validation.exceptions import PhysicalValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_machine


class TestMachineValidation(unittest.TestCase):
    """Unit tests for Machine validation."""

    def test_valid_machine(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=20.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        validate_machine(mach)

    def test_capacity_non_positive(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=0.0,
            min_load_rate=0.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_machine(mach)

    def test_min_load_negative(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=-10.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_machine(mach)

    def test_min_load_exceeds_capacity(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=120.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_machine(mach)

    def test_fixed_power_negative(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=20.0,
            fixed_power=-1.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": 0.5},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_machine(mach)

    def test_negative_variable_energy(self):
        mach = Machine(
            machine_id="M1",
            capacity_rate=100.0,
            min_load_rate=20.0,
            fixed_power=5.0,
            initial_state=0,
            compatible_processes=["P1"],
            variable_energy={"P1": -0.5},
        )
        with self.assertRaises(PhysicalValidationError):
            validate_machine(mach)


if __name__ == "__main__":
    unittest.main()
