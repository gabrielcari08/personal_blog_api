"""Entidad de dominio para el usuario."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.exceptions.user_exceptions import UserValidationException

# Limites de negocio segun la especificacion.
USERNAME_MIN_LENGTH = 8
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 20

# Roles permitidos en esta version.
ALLOWED_ROLES = ("USER", "ADMIN")


def validate_plain_password(password: str) -> None:
    """Valida la longitud de la clave en texto plano sin recortarla."""
    # Valida que la contraseña no este vacia
    if not isinstance(password, str) or password == "":
        raise UserValidationException("Password is required.")
    # Valida que la contraseña contenga entre 8 y 20 caracteres.
    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        raise UserValidationException("Password must be 8-20 characters.")


# Definicion del usuario como entidad de dominio.
@dataclass
class User:
    """Representa un usuario del blog con sus invariantes de negocio."""

    username: str
    email: str
    password_hash: str
    id: Optional[int] = None
    role: str = "USER"
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Valida los invariantes despues de construir la entidad."""
        self._validate_username(self.username)
        self._validate_email(self.email)
        self._validate_password_hash(self.password_hash)
        self._validate_role(self.role)

    @staticmethod
    def _validate_username(username: str) -> None:
        """Valida presencia, longitud y ausencia de blancos en username."""
        if not isinstance(username, str) or username == "":
            raise UserValidationException("Username is required.")
        # Nunca se recorta: cualquier blanco (incluidos extremos) invalida.
        if any(char.isspace() for char in username):
            raise UserValidationException("Username must not contain whitespace.")
        if len(username) < USERNAME_MIN_LENGTH or len(username) > USERNAME_MAX_LENGTH:
            raise UserValidationException("Username must be 8-20 characters.")

    @staticmethod
    def _validate_email(email: str) -> None:
        """Valida presencia minima del correo (el formato se valida en el borde)."""
        if not isinstance(email, str) or email.strip() == "":
            raise UserValidationException("Email is required.")

    @staticmethod
    def _validate_password_hash(password_hash: str) -> None:
        """Valida que exista un hash almacenado (nunca la clave en plano)."""
        if not isinstance(password_hash, str) or password_hash == "":
            raise UserValidationException("Password hash is required.")

    @staticmethod
    def _validate_role(role: str) -> None:
        """Valida que el rol sea USER o ADMIN."""
        if role not in ALLOWED_ROLES:
            raise UserValidationException("Role must be USER or ADMIN.")
