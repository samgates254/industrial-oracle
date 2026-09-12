import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for ElectricalParameters validation."""

import unittest
from industrial_oracle.domain.electrical import ElectricalParameters
from industrial_oracle.validation.exceptions import PhysicalValidationError
from industrial_oracle.validation.physical import validate_electrical


class TestElectricalValidation(unittest.TestCase):
    """Unit tests for ElectricalParameters validation."""

    def test_valid_electrical(self):
        elec = ElectricalParameters(power_factor=0.80, contract_limit_kva=100.0)
        validate_electrical(elec)

    def test_power_factor_zero_or_negative(self):
        with self.assertRaises(PhysicalValidationError):
            validate_electrical(ElectricalParameters(power_factor=0.0, contract_limit_kva=100.0))
        with self.assertRaises(PhysicalValidationError):
            validate_electrical(ElectricalParameters(power_factor=-0.5, contract_limit_kva=100.0))

    def test_power_factor_greater_than_one(self):
        with self.assertRaises(PhysicalValidationError):
            validate_electrical(ElectricalParameters(power_factor=1.05, contract_limit_kva=100.0))

    def test_contract_limit_non_positive(self):
        with self.assertRaises(PhysicalValidationError):
            validate_electrical(ElectricalParameters(power_factor=0.80, contract_limit_kva=0.0))
        with self.assertRaises(PhysicalValidationError):
            validate_electrical(ElectricalParameters(power_factor=0.80, contract_limit_kva=-50.0))


if __name__ == "__main__":
    unittest.main()
