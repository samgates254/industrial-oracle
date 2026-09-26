"""Phase 4 migration: Operational Execution, Work Orders, Runs, Maintenance, and Inventory.

Revision ID: 0004_operational_execution
Revises: 0003_assets_production_lines_machines
Create Date: 2026-09-12 16:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_operational_execution"
down_revision: Union[str, None] = "0003_assets_production_lines_machines"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update work_orders table
    op.add_column("work_orders", sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True))
    op.add_column("work_orders", sa.Column("production_line_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("production_lines.id", ondelete="SET NULL"), nullable=True))
    op.add_column("work_orders", sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True))
    op.add_column("work_orders", sa.Column("work_order_number", sa.String(length=50), nullable=True))
    op.add_column("work_orders", sa.Column("work_order_type", sa.String(length=50), nullable=False, server_default="PRODUCTION"))
    op.add_column("work_orders", sa.Column("planned_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("work_orders", sa.Column("planned_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("work_orders", sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("work_orders", sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("work_orders", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("work_orders", sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("work_orders", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_work_orders_org_number", "work_orders", ["organization_id", "work_order_number"], unique=True)

    # 2. Update production_runs table
    op.add_column("production_runs", sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=True))
    op.add_column("production_runs", sa.Column("plant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plants.id", ondelete="CASCADE"), nullable=True))
    op.add_column("production_runs", sa.Column("machine_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("machines.id", ondelete="SET NULL"), nullable=True))
    op.add_column("production_runs", sa.Column("work_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("work_orders.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("production_runs", sa.Column("run_number", sa.String(length=50), nullable=True))
    op.add_column("production_runs", sa.Column("product_code", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("production_runs", sa.Column("planned_quantity", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("production_runs", sa.Column("actual_quantity", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("production_runs", sa.Column("rejected_quantity", sa.Float(), nullable=False, server_default="0.0"))
    op.add_column("production_runs", sa.Column("unit_of_measure", sa.String(length=50), nullable=False, server_default="UNITS"))
    op.add_column("production_runs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("production_runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("production_runs", sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("production_runs", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("production_runs", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.create_index("ix_production_runs_org_number", "production_runs", ["organization_id", "run_number"], unique=True)

    # 3. Create maintenance_work_orders table
    op.create_table(
        "maintenance_work_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("machines.id", ondelete="SET NULL"), nullable=True),
        sa.Column("maintenance_type", sa.String(length=50), nullable=False, server_default="CORRECTIVE"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PLANNED"),
        sa.Column("fault_description", sa.Text(), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("technician_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("downtime_minutes", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("maintenance_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maintenance_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maint_wo_org_status", "maintenance_work_orders", ["organization_id", "status"])

    # 4. Create items table
    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="RAW_MATERIAL"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_items_org_sku", "items", ["organization_id", "sku"], unique=True)
    op.create_index("ix_items_org_category", "items", ["organization_id", "category"])

    # 5. Create inventory_locations table
    op.create_table(
        "inventory_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inv_loc_org_site_code", "inventory_locations", ["organization_id", "site_id", "code"], unique=True)

    # 6. Create inventory_balances table
    op.create_table(
        "inventory_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reserved_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inv_balances_org_item_loc", "inventory_balances", ["organization_id", "item_id", "location_id"], unique=True)

    # 7. Create inventory_transactions table
    op.create_table(
        "inventory_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_inv_tx_org_item", "inventory_transactions", ["organization_id", "item_id"])

    # 8. Create material_consumptions table
    op.create_table(
        "material_consumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consumer_type", sa.String(length=50), nullable=False),
        sa.Column("consumer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("inventory_transaction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_transactions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("consumed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mat_consumptions_consumer", "material_consumptions", ["consumer_type", "consumer_id"])
    op.create_index("ix_mat_consumptions_org", "material_consumptions", ["organization_id"])


def downgrade() -> None:
    op.drop_table("material_consumptions")
    op.drop_table("inventory_transactions")
    op.drop_table("inventory_balances")
    op.drop_table("inventory_locations")
    op.drop_table("items")
    op.drop_table("maintenance_work_orders")

    op.drop_index("ix_production_runs_org_number", table_name="production_runs")
    op.drop_column("production_runs", "version")
    op.drop_column("production_runs", "notes")
    op.drop_column("production_runs", "operator_id")
    op.drop_column("production_runs", "completed_at")
    op.drop_column("production_runs", "started_at")
    op.drop_column("production_runs", "unit_of_measure")
    op.drop_column("production_runs", "rejected_quantity")
    op.drop_column("production_runs", "actual_quantity")
    op.drop_column("production_runs", "planned_quantity")
    op.drop_column("production_runs", "product_code")
    op.drop_column("production_runs", "run_number")
    op.drop_column("production_runs", "work_order_id")
    op.drop_column("production_runs", "machine_id")
    op.drop_column("production_runs", "plant_id")
    op.drop_column("production_runs", "site_id")

    op.drop_index("ix_work_orders_org_number", table_name="work_orders")
    op.drop_column("work_orders", "version")
    op.drop_column("work_orders", "assigned_to")
    op.drop_column("work_orders", "created_by")
    op.drop_column("work_orders", "actual_end")
    op.drop_column("work_orders", "actual_start")
    op.drop_column("work_orders", "planned_end")
    op.drop_column("work_orders", "planned_start")
    op.drop_column("work_orders", "work_order_type")
    op.drop_column("work_orders", "work_order_number")
    op.drop_column("work_orders", "asset_id")
    op.drop_column("work_orders", "production_line_id")
    op.drop_column("work_orders", "site_id")
