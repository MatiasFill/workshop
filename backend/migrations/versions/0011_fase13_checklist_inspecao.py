"""fase13_checklist_inspecao

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-17

Cria work_order_checklist_items (FASE 13): checklist de inspeção veicular
dentro da Ordem de Serviço, item pendente do P1 (orçamento/OS/checklist)
desde a especificação original. Mesmo padrão de RLS das migrations
0002-0010.
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

TABLES = ["work_order_checklist_items"]


def upgrade() -> None:
    op.create_table(
        "work_order_checklist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="NOT_CHECKED"),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
        sa.Column("checked_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("checked_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_work_order_checklist_items_company_id", "work_order_checklist_items", ["company_id"])
    op.create_index(
        "ix_work_order_checklist_items_work_order_id", "work_order_checklist_items", ["work_order_id"]
    )

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

    op.drop_table("work_order_checklist_items")
