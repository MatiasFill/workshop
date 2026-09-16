"""fase11_fila_notificacoes

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-14

Cria a tabela da FASE 11 (fila de reenvio de notificações com retry/backoff
e idempotência) e ativa RLS no PostgreSQL, mesmo padrão das migrations
0002 a 0009.
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

TABLES = ["notification_requests"]


def upgrade() -> None:
    op.create_table(
        "notification_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="PENDING"),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("work_order_id", sa.Integer, sa.ForeignKey("work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False, server_default=""),
        sa.Column("message", sa.String(2000), nullable=False, server_default=""),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("next_attempt_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("last_error", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "idempotency_key", name="uq_notification_requests_company_idem_key"),
    )
    op.create_index("ix_notification_requests_company_id", "notification_requests", ["company_id"])
    # Acelera o "puxar o próximo lote pendente" do worker/cron.
    op.create_index(
        "ix_notification_requests_due", "notification_requests", ["company_id", "status", "next_attempt_at"]
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

    op.drop_table("notification_requests")
