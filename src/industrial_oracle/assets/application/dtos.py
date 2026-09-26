"""Assets, Production Lines, Machines, and Telemetry DTOs."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Asset DTOs
# ==============================================================================

class AssetCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, description="Human-readable asset title")
    asset_tag: str = Field(..., min_length=2, description="Unique asset barcode / tag")
    asset_type: str = Field(..., description="Classification category (e.g. MECHANICAL, ELECTRICAL)")
    plant_id: Optional[uuid.UUID] = Field(None, description="Associated plant identifier")
    serial_number: Optional[str] = Field(None, description="Equipment manufacturer serial number")
    critical: bool = Field(False, description="Whether this is critical plant infrastructure")
    location_in_plant: Optional[str] = Field(None, description="Specific physical zone or aisle")


class AssetUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    plant_id: Optional[uuid.UUID] = None
    asset_type: Optional[str] = None
    serial_number: Optional[str] = None
    critical: Optional[bool] = None
    location_in_plant: Optional[str] = None


class AssetStatusUpdateDTO(BaseModel):
    status: str = Field(..., description="Target status (IN_SERVICE, MAINTENANCE, OUT_OF_SERVICE, DECOMMISSIONED)")


class AssetResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    plant_id: Optional[uuid.UUID] = None
    name: str
    asset_tag: str
    asset_type: str
    status: str
    serial_number: Optional[str] = None
    critical: bool
    location_in_plant: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Production Line DTOs
# ==============================================================================

class ProductionLineCreateDTO(BaseModel):
    plant_id: uuid.UUID = Field(..., description="Host plant identifier")
    name: str = Field(..., min_length=2, description="Production line title")
    code: str = Field(..., min_length=2, description="Unique line code within plant")
    capacity_units_per_hour: float = Field(0.0, ge=0.0, description="Rated production rate")


class ProductionLineResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    plant_id: uuid.UUID
    name: str
    code: str
    capacity_units_per_hour: float
    status: str
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Machine DTOs
# ==============================================================================

class MachineCreateDTO(BaseModel):
    asset_id: uuid.UUID = Field(..., description="Linked equipment asset identifier")
    name: str = Field(..., min_length=2, description="Machine name")
    production_line_id: Optional[uuid.UUID] = Field(None, description="Optional line assignment")
    model: Optional[str] = Field(None, description="Machine model or part number")
    power_rating_kw: float = Field(0.0, ge=0.0, description="Nominal power rating in kW")
    operating_hours: float = Field(0.0, ge=0.0, description="Initial operating hours counter")


class MachineUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    model: Optional[str] = None
    power_rating_kw: Optional[float] = Field(None, ge=0.0)
    production_line_id: Optional[uuid.UUID] = None


class MachineFaultDTO(BaseModel):
    fault_code: str = Field(..., min_length=2, description="Diagnostic fault code")
    description: str = Field(..., min_length=2, description="Failure description")


class MachineHoursDTO(BaseModel):
    hours: float = Field(..., ge=0.0, description="Hours to add to operating total")


class MachineResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    asset_id: uuid.UUID
    production_line_id: Optional[uuid.UUID] = None
    name: str
    model: Optional[str] = None
    power_rating_kw: float
    operating_hours: float
    status: str
    fault_code: Optional[str] = None
    fault_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==============================================================================
# Telemetry Point DTOs
# ==============================================================================

class TelemetryPointCreateDTO(BaseModel):
    metric_name: str = Field(..., min_length=2, description="Measurement metric (e.g. vibration, temp)")
    unit: str = Field(..., min_length=1, description="Engineering unit (e.g. degC, mm/s, RPM)")
    min_threshold: Optional[float] = Field(None, description="Safe operating lower bound")
    max_threshold: Optional[float] = Field(None, description="Safe operating upper bound")


class TelemetryPointResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    machine_id: uuid.UUID
    metric_name: str
    unit: str
    current_value: Optional[float] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    last_sampled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
