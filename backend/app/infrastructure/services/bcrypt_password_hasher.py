"""Cifrador de claves con Bcrypt (implementacion de infraestructura)."""

from passlib.context import CryptContext

from app.domain.services.password_hasher_service import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Implementa PasswordHasher con Passlib Bcrypt."""

    def __init__(self) -> None:
        """Configura el contexto solo con el esquema Bcrypt."""
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        """Genera el hash Bcrypt de la clave en texto plano."""
        return str(self._context.hash(plain_password))

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verifica la clave contra el hash (falso si el hash es invalido)."""
        try:
            return bool(self._context.verify(plain_password, password_hash))
        except (ValueError, TypeError):
            return False
