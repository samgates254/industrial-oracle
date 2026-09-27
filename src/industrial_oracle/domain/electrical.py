"""Electrical parameters for V0.1."""

from pydantic import BaseModel, ConfigDict


class ElectricalParameters(BaseModel):
    """Plant-wide electrical grid and power parameters."""

    power_factor: float
    contract_limit_kva: float

    model_config = ConfigDict(frozen=True)
