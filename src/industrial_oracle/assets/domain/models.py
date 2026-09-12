"""Assets, Production Lines, Machines, and Telemetry domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import AggregateRoot, Entity
from industrial_oracle.shared.domain.events import DomainEvent


class AssetStatus(str, Enum):
    IN_SERVICE = "IN_SERVICE"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    DECOMMISSIONED = "DECOMMISSIONED"


class MachineStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAULTED = "FAULTED"
    MAINTENANCE = "MAINTENANCE"


class ProductionLineStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class Asset(AggregateRoot):
    """Asset aggregate root representing physical capital equipment."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        name: str,
        asset_tag: str,
        asset_type: str,
        plant_id: Optional[uuid.UUID] = None,
        status: str = AssetStatus.IN_SERVICE.value,
        serial_number: Optional[str] = None,
        critical: bool = False,
        location_in_plant: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.plant_id = plant_id
        self.name = name.strip()
        self.asset_tag = asset_tag.strip()
        self.asset_type = asset_type.strip()
        self.status = status
        self.serial_number = serial_number
        self.critical = critical
        self.location_in_plant = location_in_plant

    # Asset Operational Status State Machine
    def send_to_maintenance(self) -> None:
        if self.status == AssetStatus.DECOMMISSIONED.value:
            raise BusinessRuleViolationException(
                "Cannot place decommissioned asset into maintenance.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old = self.status
        self.status = AssetStatus.MAINTENANCE.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="AssetStatusChanged",
                aggregate_id=str(self.id),
                aggregate_type="Asset",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status},
            )
        )

    def return_to_service(self) -> None:
        if self.status == AssetStatus.DECOMMISSIONED.value:
            raise BusinessRuleViolationException(
                "Cannot return decommissioned asset to service.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old = self.status
        self.status = AssetStatus.IN_SERVICE.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="AssetStatusChanged",
                aggregate_id=str(self.id),
                aggregate_type="Asset",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status},
            )
        )

    def take_out_of_service(self) -> None:
        if self.status == AssetStatus.DECOMMISSIONED.value:
            raise BusinessRuleViolationException(
                "Cannot take decommissioned asset out of service.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old = self.status
        self.status = AssetStatus.OUT_OF_SERVICE.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="AssetStatusChanged",
                aggregate_id=str(self.id),
                aggregate_type="Asset",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status},
            )
        )

    def decommission(self) -> None:
        if self.status == AssetStatus.DECOMMISSIONED.value:
            raise BusinessRuleViolationException(
                "Asset is already decommissioned.",
                rule_name="ALREADY_DECOMMISSIONED",
            )
        old = self.status
        self.status = AssetStatus.DECOMMISSIONED.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="AssetDecommissioned",
                aggregate_id=str(self.id),
                aggregate_type="Asset",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status},
            )
        )


class ProductionLine(AggregateRoot):
    """Production line aggregate root within an industrial plant."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        plant_id: uuid.UUID,
        name: str,
        code: str,
        capacity_units_per_hour: float = 0.0,
        status: str = ProductionLineStatus.ACTIVE.value,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.plant_id = plant_id
        self.name = name.strip()
        self.code = code.strip()
        self.capacity_units_per_hour = max(0.0, capacity_units_per_hour)
        self.status = status

    def activate(self) -> None:
        self.status = ProductionLineStatus.ACTIVE.value
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.status = ProductionLineStatus.INACTIVE.value
        self.updated_at = datetime.now(timezone.utc)

    def set_maintenance(self) -> None:
        self.status = ProductionLineStatus.MAINTENANCE.value
        self.updated_at = datetime.now(timezone.utc)


class Machine(AggregateRoot):
    """Machine aggregate root modeling operational processing equipment."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        asset_id: uuid.UUID,
        name: str,
        production_line_id: Optional[uuid.UUID] = None,
        model: Optional[str] = None,
        power_rating_kw: float = 0.0,
        operating_hours: float = 0.0,
        status: str = MachineStatus.STOPPED.value,
        fault_code: Optional[str] = None,
        fault_description: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.asset_id = asset_id
        self.production_line_id = production_line_id
        self.name = name.strip()
        self.model = model
        self.power_rating_kw = max(0.0, power_rating_kw)
        self.operating_hours = max(0.0, operating_hours)
        self.status = status
        self.fault_code = fault_code
        self.fault_description = fault_description

    # Machine Operational State Machine
    def start(self) -> None:
        if self.status == MachineStatus.RUNNING.value:
            return
        if self.status == MachineStatus.FAULTED.value:
            raise BusinessRuleViolationException(
                f"Cannot start machine in FAULTED state (code: {self.fault_code}). Clear fault first.",
                rule_name="MACHINE_FAULTED",
            )
        if self.status == MachineStatus.MAINTENANCE.value:
            raise BusinessRuleViolationException(
                "Cannot start machine while in MAINTENANCE state.",
                rule_name="MACHINE_IN_MAINTENANCE",
            )
        old = self.status
        self.status = MachineStatus.RUNNING.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="MachineStarted",
                aggregate_id=str(self.id),
                aggregate_type="Machine",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status, "power_kw": self.power_rating_kw},
            )
        )

    def stop(self) -> None:
        if self.status == MachineStatus.STOPPED.value:
            return
        old = self.status
        self.status = MachineStatus.STOPPED.value
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="MachineStopped",
                aggregate_id=str(self.id),
                aggregate_type="Machine",
                organization_id=str(self.organization_id),
                payload={"old_status": old, "new_status": self.status},
            )
        )

    def record_fault(self, fault_code: str, description: str) -> None:
        old = self.status
        self.status = MachineStatus.FAULTED.value
        self.fault_code = fault_code
        self.fault_description = description
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="MachineFaultDetected",
                aggregate_id=str(self.id),
                aggregate_type="Machine",
                organization_id=str(self.organization_id),
                payload={
                    "old_status": old,
                    "new_status": self.status,
                    "fault_code": fault_code,
                    "fault_description": description,
                },
            )
        )

    def clear_fault(self) -> None:
        if self.status != MachineStatus.FAULTED.value:
            raise BusinessRuleViolationException(
                "Machine is not in FAULTED state.",
                rule_name="NOT_FAULTED",
            )
        self.status = MachineStatus.STOPPED.value
        self.fault_code = None
        self.fault_description = None
        self.updated_at = datetime.now(timezone.utc)

    def set_maintenance(self) -> None:
        self.status = MachineStatus.MAINTENANCE.value
        self.updated_at = datetime.now(timezone.utc)

    def complete_maintenance(self) -> None:
        if self.status != MachineStatus.MAINTENANCE.value:
            raise BusinessRuleViolationException(
                "Machine is not in MAINTENANCE state.",
                rule_name="NOT_IN_MAINTENANCE",
            )
        self.status = MachineStatus.STOPPED.value
        self.updated_at = datetime.now(timezone.utc)

    def log_operating_hours(self, hours: float) -> None:
        if hours < 0:
            raise BusinessRuleViolationException(
                "Operating hours increment cannot be negative.",
                rule_name="NEGATIVE_HOURS",
            )
        self.operating_hours += hours
        self.updated_at = datetime.now(timezone.utc)


class TelemetryPoint(Entity):
    """Telemetry point channel associated with an operational machine."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        machine_id: uuid.UUID,
        metric_name: str,
        unit: str,
        current_value: Optional[float] = None,
        min_threshold: Optional[float] = None,
        max_threshold: Optional[float] = None,
        last_sampled_at: Optional[datetime] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.machine_id = machine_id
        self.metric_name = metric_name.strip()
        self.unit = unit.strip()
        self.current_value = current_value
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.last_sampled_at = last_sampled_at

    def record_sample(self, value: float, sampled_at: Optional[datetime] = None) -> None:
        self.current_value = value
        self.last_sampled_at = sampled_at or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
