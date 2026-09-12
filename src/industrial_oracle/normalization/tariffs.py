"""Canonical tariff schedule and energy rate mapping."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from industrial_oracle.domain.economics import Economics
from industrial_oracle.domain.time import TimeHorizon


@dataclass(frozen=True)
class NormalizedTariffSchedule:
    """Canonical deterministic period tariff mapping."""

    period_classes: Mapping[int, str]
    energy_rates: Mapping[int, float]


def normalize_tariffs(th: TimeHorizon, econ: Economics) -> NormalizedTariffSchedule:
    """Convert tariff partitions and economic rates into deterministic read-only mappings."""
    period_classes = {}
    energy_rates = {}

    s_peak = set(th.tariff_partition.peak_periods)
    s_offpeak = set(th.tariff_partition.offpeak_periods)
    s_shoulder = set(th.tariff_partition.shoulder_periods)

    for t in range(1, th.num_periods + 1):
        if t in s_peak:
            period_classes[t] = "PEAK"
            energy_rates[t] = float(econ.energy_tariffs.c_peak)
        elif t in s_offpeak:
            period_classes[t] = "OFFPEAK"
            energy_rates[t] = float(econ.energy_tariffs.c_offpeak)
        elif t in s_shoulder:
            period_classes[t] = "SHOULDER"
            energy_rates[t] = float(econ.energy_tariffs.c_shoulder)

    return NormalizedTariffSchedule(
        period_classes=MappingProxyType(period_classes),
        energy_rates=MappingProxyType(energy_rates),
    )
