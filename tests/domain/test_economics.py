import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Economics domain entities."""

import unittest
from industrial_oracle.domain.economics import Economics, EnergyTariffs


class TestEconomicsDomain(unittest.TestCase):
    """Economics domain representation tests."""

    def test_create_economics_parameters(self):
        """Test creation of tariffs, demand charges, and costs."""
        tariffs = EnergyTariffs(
            c_peak=30.0,
            c_offpeak=10.0,
            c_shoulder=20.0,
        )
        econ = Economics(
            energy_tariffs=tariffs,
            demand_charge_rate=500.0,
            fixed_charge=1000.0,
            purchase_costs={"RAW": 80.0},
            setup_costs={"M1": 500.0, "M2": 700.0},
            holding_costs={"RAW": 2.0, "INTERMEDIATE": 3.0, "FINISHED": 4.0},
            penalty_costs={"FINISHED": 200.0},
        )
        self.assertEqual(econ.energy_tariffs.c_peak, 30.0)
        self.assertEqual(econ.demand_charge_rate, 500.0)
        self.assertEqual(econ.fixed_charge, 1000.0)
        self.assertEqual(econ.purchase_costs["RAW"], 80.0)


if __name__ == "__main__":
    unittest.main()
