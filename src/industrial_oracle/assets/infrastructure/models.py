"""SQLAlchemy database models for assets, machines, production lines, and telemetry."""

from industrial_oracle.core.database import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    ModelBase,
    PG_UUID,
    String,
    Text,
)


class AssetModel(ModelBase):
    __tablename__ = "assets"

    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(PG_UUID(as_uuid=True), ForeignKey("plants.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    asset_tag = Column(String(100), nullable=False)
    asset_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="IN_SERVICE")
    serial_number = Column(String(100), nullable=True)
    critical = Column(Boolean, nullable=False, default=False)
    location_in_plant = Column(String(255), nullable=True)


class ProductionLineModel(ModelBase):
    __tablename__ = "production_lines"

    plant_id = Column(PG_UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    capacity_units_per_hour = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="ACTIVE")


class MachineModel(ModelBase):
    __tablename__ = "machines"

    asset_id = Column(PG_UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    production_line_id = Column(PG_UUID(as_uuid=True), ForeignKey("production_lines.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    model = Column(String(100), nullable=True)
    power_rating_kw = Column(Float, nullable=False, default=0.0)
    operating_hours = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="STOPPED")
    fault_code = Column(String(100), nullable=True)
    fault_description = Column(Text, nullable=True)


class TelemetryPointModel(ModelBase):
    __tablename__ = "telemetry_points"

    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    machine_id = Column(PG_UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=False)
    current_value = Column(Float, nullable=True)
    min_threshold = Column(Float, nullable=True)
    max_threshold = Column(Float, nullable=True)
    last_sampled_at = Column(DateTime(timezone=True), nullable=True)
