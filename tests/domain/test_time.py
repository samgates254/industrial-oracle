import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Time domain entities."""

import unittest
from industrial_oracle.domain.time import TariffPartition, TimeHorizon


class TestTimeDomain(unittest.TestCase):
    """Time domain representation tests."""

    def test_create_time_horizon(self):
        """Test 4: Create 24 periods with delta_t = 1.0 h."""
        partition = TariffPartition(
            peak_periods=[9, 10, 11, 12, 18, 19, 20],
            offpeak_periods=[1, 2, 3, 4, 5, 6, 23, 24],
            shoulder_periods=[7, 8, 13, 14, 15, 16, 17, 21, 22],
        )
        th = TimeHorizon(
            num_periods=24,
            delta_t=1.0,
            tariff_partition=partition,
        )
        self.assertEqual(th.num_periods, 24)
        self.assertEqual(th.delta_t, 1.0)
        self.assertEqual(len(th.tariff_partition.peak_periods), 7)


if __name__ == "__main__":
    unittest.main()
