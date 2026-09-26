"""Material Consumption domain entity and traceability."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import Entity


class ConsumerType(str, Enum):
    PRODUCTION_RUN = "PRODUCTION_RUN"
    MAINTENANCE_WORK_ORDER = "MAINTENANCE_WORK_ORDER"


class MaterialConsumption(Entity):
    """Material consumption record linking execution tasks to inventory items."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        consumer_type: str,
        consumer_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
        quantity: float,
        inventory_transaction_id: uuid.UUID,
        consumed_by: uuid.UUID,
        id: Optional[uuid.UUID] = None,
        consumed_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=consumed_at)
        if quantity <= 0:
            raise BusinessRuleViolationException(
                "Consumed material quantity must be strictly positive.",
                rule_name="INVALID_QUANTITY",
            )
        self.organization_id = organization_id
        self.consumer_type = consumer_type
        self.consumer_id = consumer_id
        self.item_id = item_id
        self.location_id = location_id
        self.quantity = float(quantity)
        self.inventory_transaction_id = inventory_transaction_id
        self.consumed_by = consumed_by
        self.consumed_at = consumed_at or datetime.now(timezone.utc)
