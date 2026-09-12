"""Data Transfer Objects for Operations (Work Orders, Production Runs, and Material Consumption)."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class WorkOrderCreateDTO(BaseModel):
    site_id: uuid.UUID
    plant_id: uuid.UUID
    work_order_number: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    work_order_type: str = "PRODUCTION"
    priority: str = "MEDIUM"
    production_line_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None


class WorkOrderUpdateDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    production_line_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None


class WorkOrderActionDTO(BaseModel):
    reason: Optional[str] = None


class WorkOrderResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    plant_id: uuid.UUID
    production_line_id: Optional[uuid.UUID] = None
    machine_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None
    work_order_number: str
    title: str
    description: Optional[str] = None
    work_order_type: str
    priority: str
    status: str
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    version: int
    created_at: datetime
    updated_at: datetime


class ProductionRunCreateDTO(BaseModel):
    site_id: uuid.UUID
    plant_id: uuid.UUID
    production_line_id: uuid.UUID
    work_order_id: uuid.UUID
    run_number: str = Field(..., min_length=2, max_length=50)
    product_code: str = Field(..., min_length=1, max_length=100)
    planned_quantity: float = Field(..., ge=0.0)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    machine_id: Optional[uuid.UUID] = None
    operator_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class ProductionQuantityRecordDTO(BaseModel):
    good_quantity: float = Field(..., ge=0.0)
    rejected_quantity: float = Field(default=0.0, ge=0.0)


class ProductionRunActionDTO(BaseModel):
    reason: Optional[str] = None


class ProductionRunResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    plant_id: uuid.UUID
    production_line_id: uuid.UUID
    machine_id: Optional[uuid.UUID] = None
    work_order_id: uuid.UUID
    run_number: str
    product_code: str
    planned_quantity: float
    actual_quantity: float
    rejected_quantity: float
    unit_of_measure: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    operator_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime


class MaterialConsumeDTO(BaseModel):
    item_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float = Field(..., gt=0.0)


class MaterialConsumptionResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    consumer_type: str
    consumer_id: uuid.UUID
    item_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float
    inventory_transaction_id: uuid.UUID
    consumed_by: uuid.UUID
    consumed_at: datetime
