import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Electrical domain entity."""

import unittest
from industrial_oracle.domain.electrical import ElectricalParameters


class TestElectricalDomain(unittest.TestCase):
    """Electrical domain representation tests."""

    def test_create_electrical_parameters(self):
        """Test 5: Create power factor = 0.80 and contract limit = 100 kVA."""
        elec = ElectricalParameters(
            power_factor=0.80,
            contract_limit_kva=100.0,
        )
        self.assertEqual(elec.power_factor, 0.80)
        self.assertEqual(elec.contract_limit_kva, 100.0)


if __name__ == "__main__":
    unittest.main()
