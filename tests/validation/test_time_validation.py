import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for TimeHorizon and TariffPartition validation."""

import unittest
from industrial_oracle.domain.time import TariffPartition, TimeHorizon
from industrial_oracle.validation.exceptions import PhysicalValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_time_horizon


class TestTimeValidation(unittest.TestCase):
    """Unit tests for TimeHorizon validation."""

    def test_valid_time_horizon(self):
        th = TimeHorizon(
            num_periods=6,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1, 2],
                offpeak_periods=[3, 4],
                shoulder_periods=[5, 6],
            ),
        )
        validate_time_horizon(th)

    def test_num_periods_zero(self):
        th = TimeHorizon(
            num_periods=0,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[],
                offpeak_periods=[],
                shoulder_periods=[],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_delta_t_non_positive(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=0.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_period_zero(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[0],
                offpeak_periods=[1, 2],
                shoulder_periods=[3],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_period_outside_num_periods(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[4],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_overlapping_tariff_classes(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1, 2],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_duplicate_in_single_tariff_class(self):
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1, 1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_missing_tariff_periods(self):
        th = TimeHorizon(
            num_periods=4,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        with self.assertRaises(PhysicalValidationError):
            validate_time_horizon(th)

    def test_non_list_tariff_partition_raises_schema_error(self):
        """Regression test for M1.2.1: Non-list partition raises SchemaValidationError."""
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        object.__setattr__(th.tariff_partition, 'peak_periods', 'not_a_list')
        with self.assertRaises(SchemaValidationError):
            validate_time_horizon(th)

    def test_non_int_period_raises_schema_error(self):
        """Regression test for M1.2.1: Non-int period identifier raises SchemaValidationError."""
        th = TimeHorizon(
            num_periods=3,
            delta_t=1.0,
            tariff_partition=TariffPartition(
                peak_periods=[1],
                offpeak_periods=[2],
                shoulder_periods=[3],
            ),
        )
        object.__setattr__(th.tariff_partition, 'peak_periods', [True])
        with self.assertRaises(SchemaValidationError):
            validate_time_horizon(th)


if __name__ == "__main__":
    unittest.main()
