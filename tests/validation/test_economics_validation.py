import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Economics validation."""

import unittest
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.validation.exceptions import PhysicalValidationError
from industrial_oracle.validation.physical import validate_economics


class TestEconomicsValidation(unittest.TestCase):
    """Unit tests for Economics validation."""

    def _make_valid_econ(self, **kwargs):
        defaults = {
            "energy_tariffs": EnergyTariffs(c_peak=30.0, c_offpeak=10.0, c_shoulder=20.0),
            "demand_charge_rate": 500.0,
            "fixed_charge": 1000.0,
            "purchase_costs": {"RAW": 80.0},
            "setup_costs": {"M1": 500.0},
            "holding_costs": {"RAW": 2.0},
            "penalty_costs": {"FINISHED": 100.0},
        }
        defaults.update(kwargs)
        return Economics(**defaults)

    def test_valid_economics(self):
        econ = self._make_valid_econ()
        validate_economics(econ)

    def test_negative_energy_tariff(self):
        econ = self._make_valid_econ(
            energy_tariffs=EnergyTariffs(c_peak=-5.0, c_offpeak=10.0, c_shoulder=20.0)
        )
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_demand_rate(self):
        econ = self._make_valid_econ(demand_charge_rate=-100.0)
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_fixed_charge(self):
        econ = self._make_valid_econ(fixed_charge=-500.0)
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_purchase_cost(self):
        econ = self._make_valid_econ(purchase_costs={"RAW": -80.0})
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_setup_cost(self):
        econ = self._make_valid_econ(setup_costs={"M1": -50.0})
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_holding_cost(self):
        econ = self._make_valid_econ(holding_costs={"RAW": -2.0})
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)

    def test_negative_penalty_cost(self):
        econ = self._make_valid_econ(penalty_costs={"FINISHED": -10.0})
        with self.assertRaises(PhysicalValidationError):
            validate_economics(econ)


if __name__ == "__main__":
    unittest.main()
