"""
Hashing de senha com PBKDF2-HMAC-SHA256 (biblioteca padrão do Python, sem
dependência externa nova). Iterações configuráveis via
PASSWORD_HASH_ITERATIONS (padrão 600_000, recomendação atual da OWASP para
PBKDF2-SHA256).
"""
import hashlib
import hmac
import secrets

from app.core.config import settings


def hash_password(password: str) -> tuple[str, str]:
    """Retorna (hash_hex, salt_hex)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), settings.PASSWORD_HASH_ITERATIONS
    )
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), settings.PASSWORD_HASH_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), password_hash)
