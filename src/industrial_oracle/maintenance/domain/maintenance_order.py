"""Maintenance Work Order domain model and machine state coordination."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import AggregateRoot
from industrial_oracle.shared.domain.events import DomainEvent


class MaintenanceType(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    INSPECTION = "INSPECTION"
    EMERGENCY_REPAIR = "EMERGENCY_REPAIR"


class MaintenanceStatus(str, Enum):
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MaintenanceWorkOrder(AggregateRoot):
    """Maintenance Work Order aggregate built on top of the Work Order core."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        work_order_id: uuid.UUID,
        maintenance_type: str,
        fault_description: str,
        asset_id: Optional[uuid.UUID] = None,
        machine_id: Optional[uuid.UUID] = None,
        status: str = MaintenanceStatus.PLANNED.value,
        failure_code: Optional[str] = None,
        root_cause: Optional[str] = None,
        corrective_action: Optional[str] = None,
        technician_id: Optional[uuid.UUID] = None,
        downtime_minutes: float = 0.0,
        maintenance_started_at: Optional[datetime] = None,
        maintenance_completed_at: Optional[datetime] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        if not asset_id and not machine_id:
            raise BusinessRuleViolationException(
                "Maintenance work order must be associated with at least an Asset or a Machine.",
                rule_name="MISSING_EQUIPMENT_REFERENCE",
            )
        self.organization_id = organization_id
        self.work_order_id = work_order_id
        self.asset_id = asset_id
        self.machine_id = machine_id
        self.maintenance_type = maintenance_type
        self.fault_description = fault_description.strip()
        self.status = status
        self.failure_code = failure_code
        self.root_cause = root_cause
        self.corrective_action = corrective_action
        self.technician_id = technician_id
        self.downtime_minutes = max(0.0, downtime_minutes)
        self.maintenance_started_at = maintenance_started_at
        self.maintenance_completed_at = maintenance_completed_at

    def assign(self, technician_id: uuid.UUID) -> None:
        """Assign maintenance to technician."""
        if self.status in (MaintenanceStatus.COMPLETED.value, MaintenanceStatus.CANCELLED.value):
            raise BusinessRuleViolationException(
                f"Cannot assign maintenance work order in terminal status '{self.status}'.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        self.technician_id = technician_id
        if self.status == MaintenanceStatus.PLANNED.value:
            self.status = MaintenanceStatus.ASSIGNED.value
        self.updated_at = datetime.now(timezone.utc)

    def start(self) -> None:
        """Transition maintenance to IN_PROGRESS."""
        if self.status not in (MaintenanceStatus.PLANNED.value, MaintenanceStatus.ASSIGNED.value):
            raise BusinessRuleViolationException(
                f"Cannot start maintenance order in status '{self.status}'. Must be PLANNED or ASSIGNED.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = MaintenanceStatus.IN_PROGRESS.value
        self.maintenance_started_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="MaintenanceStarted",
                aggregate_id=str(self.id),
                aggregate_type="MaintenanceWorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_id": str(self.work_order_id),
                    "asset_id": str(self.asset_id) if self.asset_id else None,
                    "machine_id": str(self.machine_id) if self.machine_id else None,
                    "old_status": old_status,
                    "new_status": self.status,
                    "started_at": self.maintenance_started_at.isoformat(),
                },
            )
        )

    def complete(
        self,
        corrective_action: Optional[str] = None,
        root_cause: Optional[str] = None,
        downtime_minutes: float = 0.0,
    ) -> None:
        """Mark maintenance completed."""
        if self.status != MaintenanceStatus.IN_PROGRESS.value:
            raise BusinessRuleViolationException(
                f"Cannot complete maintenance in status '{self.status}'. Must be IN_PROGRESS.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = MaintenanceStatus.COMPLETED.value
        if corrective_action:
            self.corrective_action = corrective_action
        if root_cause:
            self.root_cause = root_cause
        self.downtime_minutes = max(self.downtime_minutes, downtime_minutes)
        self.maintenance_completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="MaintenanceCompleted",
                aggregate_id=str(self.id),
                aggregate_type="MaintenanceWorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_id": str(self.work_order_id),
                    "asset_id": str(self.asset_id) if self.asset_id else None,
                    "machine_id": str(self.machine_id) if self.machine_id else None,
                    "old_status": old_status,
                    "new_status": self.status,
                    "downtime_minutes": self.downtime_minutes,
                    "completed_at": self.maintenance_completed_at.isoformat(),
                },
            )
        )

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel maintenance work order."""
        if self.status in (MaintenanceStatus.COMPLETED.value, MaintenanceStatus.CANCELLED.value):
            raise BusinessRuleViolationException(
                f"Cannot cancel maintenance work order in terminal status '{self.status}'.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        self.status = MaintenanceStatus.CANCELLED.value
        self.updated_at = datetime.now(timezone.utc)
