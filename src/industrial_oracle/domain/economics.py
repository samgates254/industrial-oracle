"""Economic parameters and tariff structure for V0.1."""

from typing import Mapping
from pydantic import BaseModel


class EnergyTariffs(BaseModel):
    """Energy tariffs across partition classes."""

    c_peak: float
    c_offpeak: float
    c_shoulder: float

    class Config:
        frozen = True


class Economics(BaseModel):
    """Cost coefficients and economic parameters for optimization horizon."""

    energy_tariffs: EnergyTariffs
    demand_charge_rate: float
    fixed_charge: float
    purchase_costs: Mapping[str, float]
    setup_costs: Mapping[str, float]
    holding_costs: Mapping[str, float]
    penalty_costs: Mapping[str, float]

    class Config:
        frozen = True
