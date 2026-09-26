"""Inventory domain models, balance tracking, and immutable transaction ledger."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.shared.domain.entity import AggregateRoot, Entity
from industrial_oracle.shared.domain.events import DomainEvent


class ItemCategory(str, Enum):
    RAW_MATERIAL = "RAW_MATERIAL"
    SPARE_PART = "SPARE_PART"
    WIP = "WIP"
    FINISHED_GOOD = "FINISHED_GOOD"
    CONSUMABLE = "CONSUMABLE"


class TransactionType(str, Enum):
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN = "RETURN"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class Item(Entity):
    """Stock-keeping item or material definition within an organization."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        sku: str,
        name: str,
        unit_of_measure: str,
        category: str = ItemCategory.RAW_MATERIAL.value,
        description: Optional[str] = None,
        active: bool = True,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.sku = sku.strip().upper()
        self.name = name.strip()
        self.unit_of_measure = unit_of_measure.strip()
        self.category = category
        self.description = description
        self.active = active

    def deactivate(self) -> None:
        self.active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        self.active = True
        self.updated_at = datetime.now(timezone.utc)


class InventoryLocation(Entity):
    """Physical or logical storage location in a site/plant."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        site_id: uuid.UUID,
        code: str,
        name: str,
        plant_id: Optional[uuid.UUID] = None,
        active: bool = True,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.site_id = site_id
        self.plant_id = plant_id
        self.code = code.strip().upper()
        self.name = name.strip()
        self.active = active


class InventoryBalance(AggregateRoot):
    """Inventory quantity balance aggregate with concurrency versioning."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
        quantity: float = 0.0,
        reserved_quantity: float = 0.0,
        version: int = 1,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        if quantity < 0:
            raise BusinessRuleViolationException(
                "Inventory balance cannot be negative.",
                rule_name="NEGATIVE_INVENTORY",
            )
        if reserved_quantity < 0:
            raise BusinessRuleViolationException(
                "Reserved inventory quantity cannot be negative.",
                rule_name="NEGATIVE_RESERVATION",
            )
        if reserved_quantity > quantity:
            raise BusinessRuleViolationException(
                "Reserved quantity cannot exceed total on-hand quantity.",
                rule_name="OVER_RESERVATION",
            )
        self.organization_id = organization_id
        self.item_id = item_id
        self.location_id = location_id
        self.quantity = float(quantity)
        self.reserved_quantity = float(reserved_quantity)
        self.version = version

    @property
    def available_quantity(self) -> float:
        return max(0.0, self.quantity - self.reserved_quantity)

    def increase(self, amount: float) -> None:
        """Increase stock balance."""
        if amount <= 0:
            raise BusinessRuleViolationException(
                "Increase quantity must be positive.",
                rule_name="INVALID_QUANTITY",
            )
        self.quantity += amount
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def decrease(self, amount: float) -> None:
        """Decrease stock balance ensuring non-negative available quantity."""
        if amount <= 0:
            raise BusinessRuleViolationException(
                "Decrease quantity must be positive.",
                rule_name="INVALID_QUANTITY",
            )
        if self.available_quantity < amount:
            raise BusinessRuleViolationException(
                f"Insufficient inventory available (requested {amount}, available {self.available_quantity}).",
                rule_name="INSUFFICIENT_INVENTORY",
            )
        self.quantity -= amount
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)

    def adjust(self, new_quantity: float) -> float:
        """Directly adjust stock balance to new physical count. Returns delta."""
        if new_quantity < 0:
            raise BusinessRuleViolationException(
                "Stock balance cannot be adjusted to negative.",
                rule_name="NEGATIVE_INVENTORY",
            )
        delta = new_quantity - self.quantity
        self.quantity = new_quantity
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        return delta


class InventoryTransaction(Entity):
    """Immutable ledger record of inventory movement."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
        transaction_type: str,
        quantity: float,
        created_by: uuid.UUID,
        reference_type: Optional[str] = None,
        reference_id: Optional[uuid.UUID] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)
        self.organization_id = organization_id
        self.item_id = item_id
        self.location_id = location_id
        self.transaction_type = transaction_type
        self.quantity = float(quantity)
        self.created_by = created_by
        self.reference_type = reference_type
        self.reference_id = reference_id
