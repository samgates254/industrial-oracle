"""Demand domain entity for V0.1."""

from pydantic import BaseModel


class DemandOrder(BaseModel):
    """Discrete period demand order for finished resources."""

    resource_id: str
    period: int
    quantity: float

    class Config:
        frozen = True
