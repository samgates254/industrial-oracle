"""Process domain object for V0.1."""

from typing import Mapping
from pydantic import BaseModel, ConfigDict


class Process(BaseModel):
    """Process domain entity representing generic resource transformation."""

    process_id: str
    input_coefficients: Mapping[str, float]
    output_coefficients: Mapping[str, float]

    model_config = ConfigDict(frozen=True)
