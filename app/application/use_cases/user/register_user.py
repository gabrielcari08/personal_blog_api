"""Caso de uso para registrar usuarios (siempre con rol USER)."""

from app.application.dtos.user_dtos import RegisterInput, UserOutput
from app.domain.entities.user import User, validate_plain_password
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher_service import PasswordHasher


class RegisterUser:
    """Orquesta el registro: valida, verifica unicidad, cifra y guarda."""

    def __init__(self, repository: UserRepository, hasher: PasswordHasher) -> None:
        """Guarda las dependencias inyectadas (repositorio y cifrador)."""
        self._repository = repository
        self._hasher = hasher

    def execute(self, data: RegisterInput) -> UserOutput:
        """Crea un usuario activo con rol USER (nunca emite token)."""

        # trimmed_email almacena el correo sin espacios en blanco.
        trimmed_email = data.email.strip()

        # Reglas de Unicidad: username exacto, correo sin mayusculas.
        if self._repository.get_by_username(data.username) is not None:
            raise DuplicateUsernameException("Username already registered.")
        if self._repository.get_by_email_normalized(trimmed_email.lower()) is not None:
            raise DuplicateEmailException("Email already registered.")

        # Hashea la contraseña
        password_hash = self._hasher.hash(data.password)

        # Creacion de la entidad User
        # User autovalida username, role, etc., en su __post_init__
        # El rol siempre es USER: se ignora cualquier valor del cliente.
        user = User(
            username=data.username,
            email=trimmed_email,
            password_hash=password_hash,
        )
        saved = self._repository.save(user)

        return UserOutput(
            id=saved.id,
            username=saved.username,
            email=saved.email,
            role=saved.role,  # type: ignore[arg-type]
        )