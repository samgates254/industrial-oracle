"""SQLAlchemy declarative models for Operations bounded context."""

from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from industrial_oracle.core.database import Base


class WorkOrderModel(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        Index("ix_work_orders_org_number", "organization_id", "work_order_number", unique=True),
        Index("ix_work_orders_org_status", "organization_id", "status"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    production_line_id = Column(UUID(as_uuid=True), ForeignKey("production_lines.id", ondelete="SET NULL"), nullable=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)

    work_order_number = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    work_order_type = Column(String(50), nullable=False, default="PRODUCTION")
    priority = Column(String(50), nullable=False, default="MEDIUM")
    status = Column(String(50), nullable=False, default="DRAFT")

    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductionRunModel(Base):
    __tablename__ = "production_runs"
    __table_args__ = (
        Index("ix_production_runs_org_number", "organization_id", "run_number", unique=True),
        Index("ix_production_runs_line_status", "production_line_id", "status"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    production_line_id = Column(UUID(as_uuid=True), ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id", ondelete="RESTRICT"), nullable=False)

    run_number = Column(String(50), nullable=False)
    product_code = Column(String(100), nullable=False)
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, nullable=False, default=0.0)
    rejected_quantity = Column(Float, nullable=False, default=0.0)
    unit_of_measure = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="PLANNED")

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    operator_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaterialConsumptionModel(Base):
    __tablename__ = "material_consumptions"
    __table_args__ = (
        Index("ix_mat_consumptions_consumer", "consumer_type", "consumer_id"),
        Index("ix_mat_consumptions_org", "organization_id"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    consumer_type = Column(String(50), nullable=False)
    consumer_id = Column(UUID(as_uuid=True), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Float, nullable=False)
    inventory_transaction_id = Column(UUID(as_uuid=True), ForeignKey("inventory_transactions.id", ondelete="RESTRICT"), nullable=False)
    consumed_by = Column(UUID(as_uuid=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
