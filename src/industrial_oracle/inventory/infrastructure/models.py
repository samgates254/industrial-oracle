"""SQLAlchemy declarative models for Inventory bounded context."""

from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from industrial_oracle.core.database import Base


class ItemModel(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_org_sku", "organization_id", "sku", unique=True),
        Index("ix_items_org_category", "organization_id", "category"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False, default="RAW_MATERIAL")
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryLocationModel(Base):
    __tablename__ = "inventory_locations"
    __table_args__ = (
        Index("ix_inv_loc_org_site_code", "organization_id", "site_id", "code", unique=True),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plants.id", ondelete="SET NULL"), nullable=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryBalanceModel(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        Index("ix_inv_balances_org_item_loc", "organization_id", "item_id", "location_id", unique=True),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    reserved_quantity = Column(Float, nullable=False, default=0.0)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryTransactionModel(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("ix_inv_tx_org_item", "organization_id", "item_id"),
        Index("ix_inv_tx_location", "location_id"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
