"""Process domain object for V0.1."""

from typing import Mapping
from pydantic import BaseModel


class Process(BaseModel):
    """Process domain entity representing generic resource transformation."""

    process_id: str
    input_coefficients: Mapping[str, float]
    output_coefficients: Mapping[str, float]

    class Config:
        frozen = True
