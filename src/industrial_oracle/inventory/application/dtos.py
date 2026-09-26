"""Data Transfer Objects for Inventory Management."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class ItemCreateDTO(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    category: str = "RAW_MATERIAL"
    description: Optional[str] = None


class ItemUpdateDTO(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class ItemResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    sku: str
    name: str
    unit_of_measure: str
    category: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class InventoryLocationCreateDTO(BaseModel):
    site_id: uuid.UUID
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    plant_id: Optional[uuid.UUID] = None


class InventoryLocationResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    plant_id: Optional[uuid.UUID] = None
    code: str
    name: str
    active: bool
    created_at: datetime
    updated_at: datetime


class InventoryReceiptDTO(BaseModel):
    item_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float = Field(..., gt=0.0)
    reference_type: Optional[str] = "PURCHASE_RECEIPT"
    reference_id: Optional[uuid.UUID] = None


class InventoryIssueDTO(BaseModel):
    item_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float = Field(..., gt=0.0)
    reference_type: Optional[str] = "MANUAL_ISSUE"
    reference_id: Optional[uuid.UUID] = None


class InventoryAdjustmentDTO(BaseModel):
    item_id: uuid.UUID
    location_id: uuid.UUID
    new_quantity: float = Field(..., ge=0.0)
    reason: Optional[str] = None


class InventoryTransferDTO(BaseModel):
    item_id: uuid.UUID
    source_location_id: uuid.UUID
    destination_location_id: uuid.UUID
    quantity: float = Field(..., gt=0.0)


class InventoryBalanceResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    item_id: uuid.UUID
    location_id: uuid.UUID
    quantity: float
    reserved_quantity: float
    available_quantity: float
    version: int
    created_at: datetime
    updated_at: datetime


class InventoryTransactionResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    item_id: uuid.UUID
    location_id: uuid.UUID
    transaction_type: str
    quantity: float
    reference_type: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    created_at: datetime
