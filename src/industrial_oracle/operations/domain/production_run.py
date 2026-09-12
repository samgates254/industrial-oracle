"""Production Run domain model, operational invariants, and state transitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import AggregateRoot
from industrial_oracle.shared.domain.events import DomainEvent


class ProductionRunStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class ProductionRun(AggregateRoot):
    """Production Run aggregate root tracking shop-floor manufacturing execution."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        site_id: uuid.UUID,
        plant_id: uuid.UUID,
        production_line_id: uuid.UUID,
        work_order_id: uuid.UUID,
        run_number: str,
        product_code: str,
        planned_quantity: float,
        unit_of_measure: str,
        machine_id: Optional[uuid.UUID] = None,
        actual_quantity: float = 0.0,
        rejected_quantity: float = 0.0,
        status: str = ProductionRunStatus.PLANNED.value,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        operator_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        version: int = 1,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        if planned_quantity < 0:
            raise BusinessRuleViolationException(
                "Planned quantity cannot be negative.",
                rule_name="NEGATIVE_QUANTITY",
            )
        if actual_quantity < 0 or rejected_quantity < 0:
            raise BusinessRuleViolationException(
                "Actual and rejected quantities cannot be negative.",
                rule_name="NEGATIVE_QUANTITY",
            )
        if rejected_quantity > actual_quantity:
            raise BusinessRuleViolationException(
                "Rejected quantity cannot exceed actual total produced quantity.",
                rule_name="INVALID_REJECTION_RATIO",
            )

        self.organization_id = organization_id
        self.site_id = site_id
        self.plant_id = plant_id
        self.production_line_id = production_line_id
        self.work_order_id = work_order_id
        self.machine_id = machine_id
        self.run_number = run_number.strip()
        self.product_code = product_code.strip()
        self.planned_quantity = planned_quantity
        self.actual_quantity = actual_quantity
        self.rejected_quantity = rejected_quantity
        self.unit_of_measure = unit_of_measure.strip()
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.operator_id = operator_id
        self.notes = notes
        self.version = version

    # --------------------------------------------------------------------------
    # Operational State Transitions
    # --------------------------------------------------------------------------

    def start(self, operator_id: Optional[uuid.UUID] = None) -> None:
        """Start production run execution."""
        if self.status != ProductionRunStatus.PLANNED.value:
            raise BusinessRuleViolationException(
                f"Cannot start production run in status '{self.status}'. Must be PLANNED.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = ProductionRunStatus.RUNNING.value
        self.started_at = datetime.now(timezone.utc)
        if operator_id:
            self.operator_id = operator_id
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionRunStarted",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "work_order_id": str(self.work_order_id),
                    "old_status": old_status,
                    "new_status": self.status,
                    "started_at": self.started_at.isoformat(),
                },
            )
        )

    def pause(self) -> None:
        """Temporarily pause execution."""
        if self.status != ProductionRunStatus.RUNNING.value:
            raise BusinessRuleViolationException(
                f"Cannot pause production run in status '{self.status}'. Must be RUNNING.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = ProductionRunStatus.PAUSED.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionRunPaused",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "old_status": old_status,
                    "new_status": self.status,
                },
            )
        )

    def resume(self) -> None:
        """Resume execution from PAUSED."""
        if self.status != ProductionRunStatus.PAUSED.value:
            raise BusinessRuleViolationException(
                f"Cannot resume production run in status '{self.status}'. Must be PAUSED.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = ProductionRunStatus.RUNNING.value
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionRunResumed",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "old_status": old_status,
                    "new_status": self.status,
                },
            )
        )

    def record_quantity(self, good_quantity: float, rejected_quantity: float = 0.0) -> None:
        """Incrementally record produced output and scrap quantities."""
        if self.status != ProductionRunStatus.RUNNING.value:
            raise BusinessRuleViolationException(
                f"Cannot record quantities while production run is in status '{self.status}'. Must be RUNNING.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        if good_quantity < 0 or rejected_quantity < 0:
            raise BusinessRuleViolationException(
                "Recorded quantities cannot be negative.",
                rule_name="NEGATIVE_QUANTITY",
            )
        increment_total = good_quantity + rejected_quantity
        self.actual_quantity += increment_total
        self.rejected_quantity += rejected_quantity
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionQuantityRecorded",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "increment_good": good_quantity,
                    "increment_rejected": rejected_quantity,
                    "total_actual": self.actual_quantity,
                    "total_rejected": self.rejected_quantity,
                },
            )
        )

    def complete(self) -> None:
        """Complete the production run."""
        if self.status not in (ProductionRunStatus.RUNNING.value, ProductionRunStatus.PAUSED.value):
            raise BusinessRuleViolationException(
                f"Cannot complete production run in status '{self.status}'. Must be RUNNING or PAUSED.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = ProductionRunStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionRunCompleted",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "actual_quantity": self.actual_quantity,
                    "rejected_quantity": self.rejected_quantity,
                    "completed_at": self.completed_at.isoformat(),
                },
            )
        )

    def abort(self, reason: str) -> None:
        """Abort the production run."""
        if self.status in (ProductionRunStatus.COMPLETED.value, ProductionRunStatus.ABORTED.value):
            raise BusinessRuleViolationException(
                f"Cannot abort production run in terminal status '{self.status}'.",
                rule_name="INVALID_STATE_TRANSITION",
            )
        old_status = self.status
        self.status = ProductionRunStatus.ABORTED.value
        self.completed_at = datetime.now(timezone.utc)
        if not self.notes:
            self.notes = f"Aborted: {reason}"
        else:
            self.notes += f" | Aborted: {reason}"
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.record_event(
            DomainEvent(
                event_type="ProductionRunAborted",
                aggregate_id=str(self.id),
                aggregate_type="ProductionRun",
                organization_id=str(self.organization_id),
                payload={
                    "run_number": self.run_number,
                    "old_status": old_status,
                    "new_status": self.status,
                    "reason": reason,
                },
            )
        )
