"""fase9_lgpd_anonimizacao

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-14

Adiciona a `customers` as colunas usadas pelo direito de exclusão/
anonimização da LGPD (art. 18) — ver app/services/lgpd.py. Nenhuma tabela
nova, nenhuma mudança de RLS (customers já está coberta desde a migration
0003).
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("is_anonymized", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.add_column("customers", sa.Column("anonymized_at", sa.DateTime, nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "anonymized_at")
    op.drop_column("customers", "is_anonymized")
