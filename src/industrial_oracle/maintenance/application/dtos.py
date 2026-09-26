"""Data Transfer Objects for Maintenance Execution."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class MaintenanceOrderCreateDTO(BaseModel):
    site_id: uuid.UUID
    plant_id: uuid.UUID
    work_order_number: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=255)
    maintenance_type: str = "CORRECTIVE"
    fault_description: str = Field(..., min_length=2)
    asset_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None
    priority: str = "HIGH"
    failure_code: Optional[str] = None
    technician_id: Optional[uuid.UUID] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


class MaintenanceOrderUpdateDTO(BaseModel):
    title: Optional[str] = None
    fault_description: Optional[str] = None
    priority: Optional[str] = None
    failure_code: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    technician_id: Optional[uuid.UUID] = None


class MaintenanceCompleteDTO(BaseModel):
    corrective_action: Optional[str] = None
    root_cause: Optional[str] = None
    downtime_minutes: float = Field(default=0.0, ge=0.0)


class MaintenanceOrderResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    work_order_id: uuid.UUID
    work_order_number: str
    title: str
    maintenance_type: str
    status: str
    priority: str
    fault_description: str
    asset_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None
    failure_code: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    technician_id: Optional[uuid.UUID] = None
    downtime_minutes: float
    maintenance_started_at: Optional[datetime] = None
    maintenance_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
