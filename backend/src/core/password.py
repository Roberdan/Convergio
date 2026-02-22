"""Password hashing helpers powered by bcrypt via passlib."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_password_context():
    from passlib.context import CryptContext

    return CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return _get_password_context().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return _get_password_context().verify(plain_password, hashed_password)
