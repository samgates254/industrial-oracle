import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for canonical unit conversion factors."""

import unittest
from industrial_oracle.normalization.units import (
    convert_mw_to_kw,
    convert_mwh_to_kwh,
    convert_tonnes_to_kg,
    MASS_UNIT,
    ENERGY_UNIT,
    ACTIVE_POWER_UNIT,
    APPARENT_POWER_UNIT,
    TIME_UNIT,
    CURRENCY_UNIT,
)


class TestCanonicalUnits(unittest.TestCase):
    """Unit conversion factor assertions."""

    def test_tonnes_to_kg(self):
        self.assertEqual(convert_tonnes_to_kg(1.0), 1000.0)
        self.assertEqual(convert_tonnes_to_kg(2.5), 2500.0)

    def test_mwh_to_kwh(self):
        self.assertEqual(convert_mwh_to_kwh(1.0), 1000.0)
        self.assertEqual(convert_mwh_to_kwh(0.75), 750.0)

    def test_mw_to_kw(self):
        self.assertEqual(convert_mw_to_kw(1.0), 1000.0)
        self.assertEqual(convert_mw_to_kw(3.2), 3200.0)

    def test_unit_constants(self):
        self.assertEqual(MASS_UNIT, "kg")
        self.assertEqual(ENERGY_UNIT, "kWh")
        self.assertEqual(ACTIVE_POWER_UNIT, "kW")
        self.assertEqual(APPARENT_POWER_UNIT, "kVA")
        self.assertEqual(TIME_UNIT, "h")
        self.assertEqual(CURRENCY_UNIT, "KSh")


if __name__ == "__main__":
    unittest.main()
