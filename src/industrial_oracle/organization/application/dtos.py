"""Organization and physical hierarchy DTOs."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class OrganizationResponseDTO(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    role_in_org: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)


class MembershipResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str
    role: str
    is_active: bool
    created_at: datetime


class SiteResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    address: Optional[str] = None
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)


class PlantResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    name: str
    code: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)
