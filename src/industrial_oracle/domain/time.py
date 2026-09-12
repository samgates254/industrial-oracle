"""Time domain objects for V0.1."""

from typing import List
from pydantic import BaseModel


class TariffPartition(BaseModel):
    """Deterministic tariff period partition for planning horizon."""

    peak_periods: List[int]
    offpeak_periods: List[int]
    shoulder_periods: List[int]

    class Config:
        frozen = True


class TimeHorizon(BaseModel):
    """Planning horizon and temporal discretization."""

    num_periods: int
    delta_t: float
    tariff_partition: TariffPartition

    class Config:
        frozen = True
