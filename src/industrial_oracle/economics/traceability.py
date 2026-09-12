"""Economic coefficient provenance and traceability models."""

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class CoefficientProvenance:
    """Auditable provenance explaining how a cost coefficient was compiled."""

    column_index: int
    symbol: str
    indices: Tuple[Any, ...]
    component: str
    rate: float
    intensity: float
    duration: float
    formula: str
    unit: str
