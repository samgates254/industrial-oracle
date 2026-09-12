"""SQLAlchemy database models for identity domain."""

from industrial_oracle.core.database import ModelBase, Column, String, Text, Boolean, ForeignKey, Index, PG_UUID


class UserModel(ModelBase):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)


class RoleModel(ModelBase):
    __tablename__ = "roles"

    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class PermissionModel(ModelBase):
    __tablename__ = "permissions"

    code = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)


class RolePermissionModel(ModelBase):
    __tablename__ = "role_permissions"

    role_id = Column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(PG_UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
