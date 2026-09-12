"""0003_assets_production_lines_machines

Revision ID: 0003_assets_production_lines_machines
Revises: 0002_identity_organization_rbac
Create Date: 2026-09-12 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_assets_production_lines_machines'
down_revision = '0002_identity_organization_rbac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enhance assets with physical location
    op.add_column('assets', sa.Column('location_in_plant', sa.String(length=255), nullable=True))
    op.create_index('ix_assets_org_status', 'assets', ['organization_id', 'status'])

    # 2. Enhance machines with fault state diagnostics
    op.add_column('machines', sa.Column('fault_code', sa.String(length=100), nullable=True))
    op.add_column('machines', sa.Column('fault_description', sa.Text(), nullable=True))
    op.create_index('ix_machines_org_status', 'machines', ['organization_id', 'status'])

    # 3. Enhance production lines with unique code per plant
    op.create_index('ix_production_lines_plant_code', 'production_lines', ['plant_id', 'code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_production_lines_plant_code', table_name='production_lines')
    op.drop_index('ix_machines_org_status', table_name='machines')
    op.drop_column('machines', 'fault_description')
    op.drop_column('machines', 'fault_code')
    op.drop_index('ix_assets_org_status', table_name='assets')
    op.drop_column('assets', 'location_in_plant')
