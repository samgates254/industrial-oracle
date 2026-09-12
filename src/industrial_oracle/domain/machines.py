"""Machine domain object for V0.1."""

from typing import List, Mapping
from pydantic import BaseModel, validator


class Machine(BaseModel):
    """Machine domain entity representing physical production asset."""

    machine_id: str
    capacity_rate: float
    min_load_rate: float
    fixed_power: float
    initial_state: int
    compatible_processes: List[str]
    variable_energy: Mapping[str, float]

    @validator("initial_state")
    def validate_initial_state_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"initial_state must be binary (0 or 1), got {v}")
        return v

    class Config:
        frozen = True
