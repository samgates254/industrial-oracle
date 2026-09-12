"""Identity application DTOs."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field

from industrial_oracle.core.security import RoleEnum
from industrial_oracle.organization.application.dtos import MembershipResponseDTO


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User plaintext password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreateDTO(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=2, description="User full name")
    role: str = Field(default=RoleEnum.VIEWER, description="Initial organization role")


class UserUpdateDTO(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    email: Optional[str] = None


class UserStatusUpdateDTO(BaseModel):
    is_active: bool = Field(..., description="Target active status")


class UserResponseDTO(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserProfileResponseDTO(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    memberships: List[MembershipResponseDTO]
    created_at: datetime
    updated_at: datetime
