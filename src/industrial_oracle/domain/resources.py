"""Resource domain object for V0.1."""

from typing import List, Optional
from pydantic import BaseModel
from .enums import ResourceCategory


class Resource(BaseModel):
    """Resource domain entity representing physical flowable stock."""

    resource_id: str
    category: ResourceCategory
    initial_stock: float
    safety_stock: float
    max_storage: float
    is_purchasable: bool
    supply_cap: Optional[List[float]] = None

    class Config:
        frozen = True
