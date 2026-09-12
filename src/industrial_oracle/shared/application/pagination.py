"""Pagination request and response schemas."""

from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    offset: int = Field(default=0, ge=0, description="Offset index")
    limit: int = Field(default=50, ge=1, le=200, description="Max items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope."""
    items: List[T]
    total: int
    offset: int
    limit: int
