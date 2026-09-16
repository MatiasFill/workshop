"""
Seed idempotente da FASE 1.

Rodar com: `python -m app.db.seed` (dentro do venv do backend, com o banco
já migrado via `alembic upgrade head`).

- Sempre garante que todos os papéis (ROLES) e permissões (PERMISSIONS) do
  catálogo existam, e que o mapeamento ROLE_PERMISSIONS esteja aplicado.
- Só cria a empresa/filial/usuário administrador inicial se
  SEED_COMPANY_NAME, SEED_ADMIN_EMAIL e SEED_ADMIN_PASSWORD estiverem
  definidos no ambiente — e só se ainda não existir nenhuma empresa.
"""
from app.core.config import settings
from app.core.passwords import hash_password
from app.core.rbac_catalog import PERMISSIONS, ROLE_PERMISSIONS, ROLES
from app.db.session import Base, SessionLocal, engine
from app.models.company import Branch, Company
from app.models.rbac import Permission, Role, RolePermission
from app.models.user import User, UserRole


def seed_roles_and_permissions(db) -> None:
    role_by_code = {r.code: r for r in db.query(Role).all()}
    for code in ROLES:
        if code not in role_by_code:
            role = Role(code=code)
            db.add(role)
            db.flush()
            role_by_code[code] = role

    perm_by_code = {p.code: p for p in db.query(Permission).all()}
    for code in PERMISSIONS:
        if code not in perm_by_code:
            perm = Permission(code=code)
            db.add(perm)
            db.flush()
            perm_by_code[code] = perm

    existing_pairs = {
        (rp.role_id, rp.permission_id) for rp in db.query(RolePermission).all()
    }
    for role_code, perm_codes in ROLE_PERMISSIONS.items():
        role = role_by_code[role_code]
        for perm_code in perm_codes:
            perm = perm_by_code[perm_code]
            if (role.id, perm.id) not in existing_pairs:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()


def seed_default_admin(db) -> None:
    if not (settings.SEED_COMPANY_NAME and settings.SEED_ADMIN_EMAIL and settings.SEED_ADMIN_PASSWORD):
        print("SEED_COMPANY_NAME/SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD não definidos — pulando seed de admin.")
        return

    if db.query(Company).count() > 0:
        print("Já existe pelo menos uma empresa — pulando seed de admin (idempotente).")
        return

    company = Company(name=settings.SEED_COMPANY_NAME)
    db.add(company)
    db.flush()

    branch = Branch(company_id=company.id, name="Matriz")
    db.add(branch)
    db.flush()

    password_hash, salt = hash_password(settings.SEED_ADMIN_PASSWORD)
    admin_role = db.query(Role).filter(Role.code == "ADMIN").one()

    user = User(
        company_id=company.id,
        branch_id=branch.id,
        name="Administrador",
        email=settings.SEED_ADMIN_EMAIL,
        password_hash=password_hash,
        password_salt=salt,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    db.commit()
    print(f"Empresa '{company.name}' e admin '{user.email}' criados.")


def main() -> None:
    Base.metadata.create_all(bind=engine)  # apenas para dev sem Alembic; em produção use migrations
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
        seed_default_admin(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
