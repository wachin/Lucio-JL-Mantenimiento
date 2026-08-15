"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("id_number", sa.String(50), nullable=True),
        sa.Column("phone_primary", sa.String(20), nullable=False),
        sa.Column("phone_secondary", sa.String(20), nullable=True),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id_number"),
    )

    op.create_table(
        "equipments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("equipment_type", sa.String(50), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("serial_number", sa.String(100), nullable=True),
        sa.Column("color", sa.String(50), nullable=True),
        sa.Column("os", sa.String(100), nullable=True),
        sa.Column("password", sa.String(100), nullable=True),
        sa.Column("accessories", sa.Text(), nullable=True),
        sa.Column("physical_state", sa.String(200), nullable=True),
        sa.Column("reported_problem", sa.Text(), nullable=True),
        sa.Column("intake_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
    )

    op.create_table(
        "service_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_number", sa.String(30), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("intake_date", sa.DateTime(), nullable=False),
        sa.Column("estimated_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("completion_date", sa.DateTime(), nullable=True),
        sa.Column("delivery_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="Recibido"),
        sa.Column("priority", sa.String(10), nullable=False, server_default="Normal"),
        sa.Column("technician", sa.String(100), nullable=True),
        sa.Column("reported_problem", sa.Text(), nullable=True),
        sa.Column("diagnosis_html", sa.Text(), nullable=True),
        sa.Column("work_done_html", sa.Text(), nullable=True),
        sa.Column("recommendations_html", sa.Text(), nullable=True),
        sa.Column("parts_used", sa.Text(), nullable=True),
        sa.Column("diagnostic_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("parts_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("labor_cost", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tax", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("advance_payment", sa.Float(), nullable=False, server_default="0"),
        sa.Column("balance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("warranty_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("budget_status", sa.String(30), nullable=True, server_default="Pendiente"),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
    )

    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("photo_type", sa.String(50), nullable=False, server_default="Otro"),
        sa.Column("capture_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
    )

    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(30), nullable=False),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("user", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
    )

    op.create_table(
        "history_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("payment_date", sa.DateTime(), nullable=False),
        sa.Column("payment_type", sa.String(30), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
    )

    op.create_table(
        "budget_concepts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("concept_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("budget_concepts")
    op.drop_table("payments")
    op.drop_table("history_events")
    op.drop_table("status_history")
    op.drop_table("photos")
    op.drop_table("service_orders")
    op.drop_table("equipments")
    op.drop_table("customers")
