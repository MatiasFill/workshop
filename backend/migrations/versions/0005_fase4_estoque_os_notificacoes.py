"""fase4_estoque_os_notificacoes

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-13

Cria as tabelas da FASE 4/5 (Estoque, Ordens de Serviço e Notificações) e
ativa RLS no PostgreSQL, mesmo padrão das migrations 0002/0003/0004.

Ordem de criação importa por causa das FKs cruzadas: stock_items antes de
work_orders (work_order_items referencia stock_items), work_orders/
work_order_items antes de stock_movements (que referencia work_orders para
rastrear a baixa automática de peças ao fechar uma OS).
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABLES = ["stock_items", "work_orders", "work_order_items", "stock_movements", "notification_logs"]


def upgrade() -> None:
    op.create_table(
        "stock_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False, server_default="un"),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("min_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("sale_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.String(1000), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "sku", name="uq_stock_items_company_sku"),
    )
    op.create_index("ix_stock_items_company_id", "stock_items", ["company_id"])

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.Integer, sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("appointment_id", sa.Integer, sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mechanic_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("diagnosis", sa.String(2000), nullable=False, server_default=""),
        sa.Column("labor_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_value", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("next_revision_date", sa.Date, nullable=True),
        sa.Column("revision_reminder_sent_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_work_orders_company_id", "work_orders", ["company_id"])
    op.create_index("ix_work_orders_customer_id", "work_orders", ["customer_id"])
    # Acelera a varredura de app/services/notifications.py -> check_upcoming_revisions.
    op.create_index(
        "ix_work_orders_next_revision", "work_orders", ["company_id", "status", "next_revision_date"]
    )

    op.create_table(
        "work_order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_item_id", sa.Integer, sa.ForeignKey("stock_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_work_order_items_company_id", "work_order_items", ["company_id"])
    op.create_index("ix_work_order_items_work_order_id", "work_order_items", ["work_order_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stock_item_id", sa.Integer, sa.ForeignKey("stock_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_company_id", "stock_movements", ["company_id"])
    op.create_index("ix_stock_movements_stock_item_id", "stock_movements", ["stock_item_id"])

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("detail", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notification_logs_company_id", "notification_logs", ["company_id"])

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (company_id = current_setting('app.current_company_id', true)::int)
            WITH CHECK (company_id = current_setting('app.current_company_id', true)::int)
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Ordem inversa da criação, por causa das FKs.
    op.drop_table("notification_logs")
    op.drop_table("stock_movements")
    op.drop_table("work_order_items")
    op.drop_table("work_orders")
    op.drop_table("stock_items")
