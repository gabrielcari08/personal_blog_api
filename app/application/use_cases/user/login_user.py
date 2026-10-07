"""Caso de uso para iniciar sesion (identificador flexible, fallo generico)."""

from typing import Protocol

from app.application.dtos.user_dtos import LoginInput, LoginOutput
from app.domain.exceptions.user_exceptions import (
    InvalidCredentialsException,
    UserValidationException,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher_service import PasswordHasher

# Mensaje unico para no revelar si fallo el identificador o la clave.
_INVALID_CREDENTIALS_MESSAGE = "Invalid credentials."


class TokenService(Protocol):
    """Contrato minimo para emitir el token de sesion sin estado."""

    def issue_token(self, user_id: str, username: str, role: str) -> str:
        """Emite un token firmado con la identidad y el rol."""
        ...


class LoginUser:
    """Autentica por email o username y devuelve un token con el rol."""

    def __init__(
        # Recibe las tres abstracciones necesarias para la autenticación:
        self,
        repository: UserRepository,  # Para buscar al usuario en la base de datos.
        hasher: PasswordHasher,  # Para verificar la contraseña.
        tokens: TokenService,  # Para emitir el token de sesion.
    ) -> None:
        """Guarda las dependencias inyectadas (repositorio, cifrador y tokens)."""
        self._repository = repository
        self._hasher = hasher
        self._tokens = tokens

    def execute(self, data: LoginInput) -> LoginOutput:
        """Valida credenciales y emite el token (mismo error generico siempre)."""
        identifier = data.identifier.strip()

        if "@" in identifier:
            # Via correo: se recorta y se normaliza a minusculas.
            user = self._repository.get_by_email_normalized(
                identifier.strip().lower()
            )
        else:
            # Via username: comparacion exacta, sin recortar.
            user = self._repository.get_by_username(identifier)

        # Evalua que el usuario exista o que la contraseña sea correcta.
        if user is None or not self._hasher.verify(data.password, user.password_hash):
            raise InvalidCredentialsException(_INVALID_CREDENTIALS_MESSAGE)

        # Genera el token con la informacion del usuario.
        token = self._tokens.issue_token(
            user_id=str(user.id),
            username=user.username,
            role=user.role,
        )
        return LoginOutput(access_token=token, token_type="bearer")
