"""fase8_audit_log

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-13

Cria a tabela da FASE 8 (trilha de auditoria) e ativa RLS no PostgreSQL,
mesmo padrão das migrations 0002 a 0007.
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

TABLES = ["audit_logs"]


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("detail", sa.String(1000), nullable=False, server_default=""),
        sa.Column("ip_address", sa.String(45), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_company_id", "audit_logs", ["company_id"])
    # Acelera a listagem por ação/entidade/usuário, ordenada por data (o uso mais comum da tela).
    op.create_index("ix_audit_logs_company_created", "audit_logs", ["company_id", "created_at"])

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

    op.drop_table("audit_logs")
