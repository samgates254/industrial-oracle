"""SQLAlchemy database models for organization domain."""

from industrial_oracle.core.database import ModelBase, Column, String, Text, Boolean, ForeignKey, Index, PG_UUID, relationship
import uuid


class OrganizationModel(ModelBase):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="ACTIVE")


class SiteModel(ModelBase):
    __tablename__ = "sites"

    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    address = Column(Text, nullable=True)
    timezone = Column(String(50), nullable=False, default="UTC")


class PlantModel(ModelBase):
    __tablename__ = "plants"

    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(PG_UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="OPERATIONAL")


class MembershipModel(ModelBase):
    __tablename__ = "memberships"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
