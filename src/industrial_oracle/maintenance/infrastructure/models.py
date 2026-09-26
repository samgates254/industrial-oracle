"""SQLAlchemy declarative models for Maintenance Execution."""

from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from industrial_oracle.core.database import Base


class MaintenanceWorkOrderModel(Base):
    __tablename__ = "maintenance_work_orders"
    __table_args__ = (
        Index("ix_maint_wo_org_status", "organization_id", "status"),
        Index("ix_maint_wo_asset", "asset_id"),
        Index("ix_maint_wo_machine", "machine_id"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="SET NULL"), nullable=True)

    maintenance_type = Column(String(50), nullable=False, default="CORRECTIVE")
    status = Column(String(50), nullable=False, default="PLANNED")
    fault_description = Column(Text, nullable=False)
    failure_code = Column(String(100), nullable=True)
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    technician_id = Column(UUID(as_uuid=True), nullable=True)
    downtime_minutes = Column(Float, nullable=False, default=0.0)

    maintenance_started_at = Column(DateTime(timezone=True), nullable=True)
    maintenance_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
