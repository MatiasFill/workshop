"""fase2_clientes_veiculos

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-10

Cria as tabelas `customers` e `vehicles` (FASE 2 — Core de negócio, P1 do
roadmap) e já ativa Row-Level Security nelas no PostgreSQL, seguindo o mesmo
padrão da migration 0002 — não faz sentido ligar RLS em 0002 e deixar de fora
as tabelas novas que também carregam `company_id`.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLES = ["customers", "vehicles"]


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("document", sa.String(20), nullable=False, server_default=""),
        sa.Column("phone", sa.String(20), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), nullable=False, server_default=""),
        sa.Column("address", sa.String(500), nullable=False, server_default=""),
        sa.Column("notes", sa.String(1000), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_customers_company_id", "customers", ["company_id"])
    # Índice único PARCIAL: só exige unicidade de documento quando ele é
    # informado (documento vazio "" é permitido em qualquer quantidade — ver
    # nota em app/models/customer.py). Uma UniqueConstraint comum quebraria no
    # segundo cliente sem documento cadastrado na mesma empresa.
    op.create_index(
        "uq_customers_company_document",
        "customers",
        ["company_id", "document"],
        unique=True,
        postgresql_where=sa.text("document != ''"),
        sqlite_where=sa.text("document != ''"),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plate", sa.String(10), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False, server_default=""),
        sa.Column("model", sa.String(100), nullable=False, server_default=""),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("color", sa.String(50), nullable=False, server_default=""),
        sa.Column("km", sa.Integer, nullable=True),
        sa.Column("notes", sa.String(1000), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "plate", name="uq_vehicles_company_plate"),
    )
    op.create_index("ix_vehicles_company_id", "vehicles", ["company_id"])
    op.create_index("ix_vehicles_customer_id", "vehicles", ["customer_id"])

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

    op.drop_table("vehicles")
    op.drop_table("customers")
