"""fase1_row_level_security

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-09

Ativa Row-Level Security no PostgreSQL para as tabelas com `company_id`, como
segunda camada de defesa além do filtro feito em código (ver app/core/deps.py
-> get_tenant_db, que faz `SET LOCAL app.current_company_id`).

Só roda em PostgreSQL: RLS não existe em SQLite, então em dev com SQLite esta
migration não faz nada (a proteção fica só na camada de aplicação nesse caso).
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TABLES = ["branches", "memory_entries", "documents", "chunks"]
# "users" fica de fora de propósito: o login consulta por e-mail (globalmente
# único, ver models/user.py) antes de sabermos a empresa do usuário — é
# exatamente isso que o login está resolvendo, então RLS na própria tabela
# `users` quebraria a consulta de login. O isolamento por empresa ali é
# garantido pela unicidade global de e-mail + pelo filtro explícito de
# company_id em qualquer outra rota que liste/edite usuários (FASE 2+).


def upgrade() -> None:
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
    if bind.dialect.name != "postgresql":
        return

    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
