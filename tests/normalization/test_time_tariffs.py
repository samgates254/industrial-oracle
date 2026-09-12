import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for Time and Tariff normalization."""

import unittest
from industrial_oracle.domain.economics import Economics, EnergyTariffs
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.normalization.tariffs import normalize_tariffs
from industrial_oracle.normalization.time import normalize_time_horizon


class TestTimeTariffsNormalization(unittest.TestCase):
    """Time horizon and deterministic tariff mapping tests."""

    def test_time_normalization_ascending(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=0.25,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        norm_time = normalize_time_horizon(th)
        self.assertEqual(norm_time.num_periods, 3)
        self.assertEqual(norm_time.delta_t, 0.25)
        self.assertEqual(norm_time.periods, (1, 2, 3))

    def test_tariff_normalization_mapping(self):
        th = TimeHorizon(
            num_periods=4,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2, 3],
                shoulder_periods=[4],
            ),
        )
        econ = Economics(
            energy_tariffs=EnergyTariffs(c_peak=35.0, c_offpeak=12.0, c_shoulder=22.0),
            demand_charge_rate=500.0,
            fixed_charge=1000.0,
            purchase_costs={},
            setup_costs={},
            holding_costs={},
            penalty_costs={},
        )
        schedule = normalize_tariffs(th, econ)
        self.assertEqual(schedule.period_classes[1], "PEAK")
        self.assertEqual(schedule.energy_rates[1], 35.0)
        self.assertEqual(schedule.period_classes[2], "OFFPEAK")
        self.assertEqual(schedule.energy_rates[2], 12.0)
        self.assertEqual(schedule.period_classes[3], "OFFPEAK")
        self.assertEqual(schedule.energy_rates[3], 12.0)
        self.assertEqual(schedule.period_classes[4], "SHOULDER")
        self.assertEqual(schedule.energy_rates[4], 22.0)


if __name__ == "__main__":
    unittest.main()
