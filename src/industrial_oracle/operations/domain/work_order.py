"""Work Order domain model and state machine."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import AggregateRoot
from industrial_oracle.shared.domain.events import DomainEvent


class WorkOrderType(str, Enum):
    PRODUCTION = "PRODUCTION"
    MAINTENANCE = "MAINTENANCE"
    INSPECTION = "INSPECTION"
    REPAIR = "REPAIR"
    SETUP = "SETUP"
    OTHER = "OTHER"


class WorkOrderPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkOrder(AggregateRoot):
    """Work Order aggregate root representing an authorized operational directive."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        site_id: uuid.UUID,
        plant_id: uuid.UUID,
        work_order_number: str,
        title: str,
        work_order_type: str = WorkOrderType.PRODUCTION.value,
        priority: str = WorkOrderPriority.MEDIUM.value,
        status: str = WorkOrderStatus.DRAFT.value,
        description: Optional[str] = None,
        production_line_id: Optional[uuid.UUID] = None,
        machine_id: Optional[uuid.UUID] = None,
        asset_id: Optional[uuid.UUID] = None,
        planned_start: Optional[datetime] = None,
        planned_end: Optional[datetime] = None,
        actual_start: Optional[datetime] = None,
        actual_end: Optional[datetime] = None,
        created_by: Optional[uuid.UUID] = None,
        assigned_to: Optional[uuid.UUID] = None,
        version: int = 1,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.site_id = site_id
        self.plant_id = plant_id
        self.work_order_number = work_order_number.strip()
        self.title = title.strip()
        self.work_order_type = work_order_type
        self.priority = priority
        self.status = status
        self.description = description
        self.production_line_id = production_line_id
        self.machine_id = machine_id
        self.asset_id = asset_id
        self.planned_start = planned_start
        self.planned_end = planned_end
        self.actual_start = actual_start
        self.actual_end = actual_end
        self.created_by = created_by
        self.assigned_to = assigned_to
        self.version = version

    # --------------------------------------------------------------------------
    # State Machine Transitions
    # --------------------------------------------------------------------------

    def release(self) -> None:
        """Release a draft work order for scheduling and execution."""
        if self.status != WorkOrderStatus.DRAFT.value:
            raise BusinessRuleViolationException(
                f"Cannot release work order in status '{self.status}'. Must be DRAFT.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.RELEASED.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="WorkOrderReleased",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                },
            )
        )

    def start(self, actual_start: Optional[datetime] = None) -> None:
        """Begin work order execution from RELEASED or ON_HOLD."""
        if self.status not in (WorkOrderStatus.RELEASED.value, WorkOrderStatus.ON_HOLD.value):
            raise BusinessRuleViolationException(
                f"Cannot start work order in status '{self.status}'. Must be RELEASED or ON_HOLD.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.IN_PROGRESS.value
        now = actual_start or datetime.now(timezone.utc)
        if not self.actual_start:
            self.actual_start = now
        self.version += 1
        self.updated_at = now
        self.record_event(
            DomainEvent(
                event_type="WorkOrderStarted",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "actual_start": self.actual_start.isoformat(),
                },
            )
        )

    def put_on_hold(self, reason: Optional[str] = None) -> None:
        """Temporarily pause work order execution."""
        if self.status != WorkOrderStatus.IN_PROGRESS.value:
            raise BusinessRuleViolationException(
                f"Cannot hold work order in status '{self.status}'. Must be IN_PROGRESS.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.ON_HOLD.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="WorkOrderPutOnHold",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "reason": reason,
                },
            )
        )

    def resume(self) -> None:
        """Resume work order from ON_HOLD back to IN_PROGRESS."""
        if self.status != WorkOrderStatus.ON_HOLD.value:
            raise BusinessRuleViolationException(
                f"Cannot resume work order in status '{self.status}'. Must be ON_HOLD.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.IN_PROGRESS.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="WorkOrderResumed",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                },
            )
        )

    def complete(self, actual_end: Optional[datetime] = None) -> None:
        """Mark work order as completed."""
        if self.status != WorkOrderStatus.IN_PROGRESS.value:
            raise BusinessRuleViolationException(
                f"Cannot complete work order in status '{self.status}'. Must be IN_PROGRESS.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.COMPLETED.value
        self.actual_end = actual_end or datetime.now(timezone.utc)
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="WorkOrderCompleted",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "actual_start": self.actual_start.isoformat() if self.actual_start else None,
                    "actual_end": self.actual_end.isoformat(),
                },
            )
        )

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel a work order if not completed or already cancelled."""
        if self.status in (WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value):
            raise BusinessRuleViolationException(
                f"Cannot cancel work order in terminal status '{self.status}'.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = WorkOrderStatus.CANCELLED.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="WorkOrderCancelled",
                aggregate_id=str(self.id),
                aggregate_type="WorkOrder",
                organization_id=str(self.organization_id),
                payload={
                    "work_order_number": self.work_order_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "reason": reason,
                },
            )
        )
