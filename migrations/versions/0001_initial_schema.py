"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, unique=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # 2. Sites
    op.create_table(
        'sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_sites_org_code', 'sites', ['organization_id', 'code'], unique=True)

    # 3. Plants
    op.create_table(
        'plants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPERATIONAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_plants_org_code', 'plants', ['organization_id', 'code'], unique=True)

    # 4. Production Lines
    op.create_table(
        'production_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('capacity_units_per_hour', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_production_lines_plant', 'production_lines', ['plant_id'])

    # 5. Assets
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('asset_tag', sa.String(length=100), nullable=False),
        sa.Column('asset_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='IN_SERVICE'),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('critical', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_assets_org_tag', 'assets', ['organization_id', 'asset_tag'], unique=True)

    # 6. Machines
    op.create_table(
        'machines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('production_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_lines.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('power_rating_kw', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('operating_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='STOPPED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_machines_line', 'machines', ['production_line_id'])

    # 7. Work Orders
    op.create_table(
        'work_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('machines.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_work_orders_org_status', 'work_orders', ['organization_id', 'status'])

    # 8. Production Runs
    op.create_table(
        'production_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('production_line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_lines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('target_quantity', sa.Float(), nullable=False),
        sa.Column('produced_quantity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_production_runs_line', 'production_runs', ['production_line_id'])

    # 9. Materials
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_materials_org_sku', 'materials', ['organization_id', 'sku'], unique=True)

    # 10. Inventory Items
    op.create_table(
        'inventory_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity_on_hand', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('min_threshold', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('max_threshold', sa.Float(), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_inventory_site_material', 'inventory_items', ['site_id', 'material_id'])

    # 11. Maintenance Plans
    op.create_table(
        'maintenance_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_name', sa.String(length=255), nullable=False),
        sa.Column('frequency_days', sa.Integer(), nullable=False),
        sa.Column('last_performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_maintenance_due', 'maintenance_plans', ['next_due_at', 'is_active'])

    # 12. Energy Meters
    op.create_table(
        'energy_meters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('machines.id', ondelete='SET NULL'), nullable=True),
        sa.Column('meter_identifier', sa.String(length=100), nullable=False),
        sa.Column('meter_type', sa.String(length=50), nullable=False),
        sa.Column('current_reading_kwh', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='kWh'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_energy_meters_org_ident', 'energy_meters', ['organization_id', 'meter_identifier'], unique=True)

    # 13. Telemetry Points
    op.create_table(
        'telemetry_points',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('machines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('min_threshold', sa.Float(), nullable=True),
        sa.Column('max_threshold', sa.Float(), nullable=True),
        sa.Column('last_sampled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_telemetry_machine_metric', 'telemetry_points', ['machine_id', 'metric_name'])

    # 14. Constraints
    op.create_table(
        'constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('constraint_type', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('expression', sa.Text(), nullable=False),
        sa.Column('bound_value', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 15. Scenarios
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 16. Optimization Runs
    op.create_table(
        'optimization_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scenarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('solver_type', sa.String(length=50), nullable=False, server_default='MILP'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('objective_value', sa.Float(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('parameters_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('result_json', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_optimization_runs_org_status', 'optimization_runs', ['organization_id', 'status'])

    # 17. Alerts
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='WARNING'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_alerts_active', 'alerts', ['organization_id', 'is_acknowledged', 'severity'])

    # 18. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_org_resource', 'audit_logs', ['organization_id', 'resource_type', 'resource_id'])
    op.create_index('ix_audit_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('alerts')
    op.drop_table('optimization_runs')
    op.drop_table('scenarios')
    op.drop_table('constraints')
    op.drop_table('telemetry_points')
    op.drop_table('energy_meters')
    op.drop_table('maintenance_plans')
    op.drop_table('inventory_items')
    op.drop_table('materials')
    op.drop_table('production_runs')
    op.drop_table('work_orders')
    op.drop_table('machines')
    op.drop_table('assets')
    op.drop_table('production_lines')
    op.drop_table('plants')
    op.drop_table('sites')
    op.drop_table('organizations')
