"""
Fixtures compartilhadas entre os testes do backend.

Requer Redis rodando para testes que fazem login de verdade (sessões vivem
lá). Ver nota em test_security.py.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_security.db")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")  # TestClient não usa HTTPS
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from app.core.passwords import hash_password
from app.core.rbac_catalog import PERMISSIONS, ROLE_PERMISSIONS, ROLES
from app.models.company import Branch, Company
from app.models.rbac import Permission, Role, RolePermission
from app.models.user import User, UserRole


def seed_test_tenant(db, role_code: str, email: str, password: str):
    """Cria uma empresa isolada + 1 usuário com um único papel, para o teste
    não depender de estado deixado por outro teste.

    Também torna a seed idempotente: se o mesmo e-mail foi usado em uma execução
    anterior, o registro antigo é removido antes de criar um novo usuário.
    """
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        db.query(UserRole).filter(UserRole.user_id == existing_user.id).delete()
        db.delete(existing_user)
        db.commit()

    company = Company(name=f"Empresa {email}")
    db.add(company)
    db.flush()
    branch = Branch(company_id=company.id, name="Matriz")
    db.add(branch)
    db.flush()

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

    existing_pairs = {(rp.role_id, rp.permission_id) for rp in db.query(RolePermission).all()}
    role = role_by_code[role_code]
    for perm_code in ROLE_PERMISSIONS[role_code]:
        perm = perm_by_code[perm_code]
        if (role.id, perm.id) not in existing_pairs:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.flush()

    password_hash, salt = hash_password(password)
    user = User(
        company_id=company.id,
        branch_id=branch.id,
        name="Usuário Teste",
        email=email,
        password_hash=password_hash,
        password_salt=salt,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return company, user
