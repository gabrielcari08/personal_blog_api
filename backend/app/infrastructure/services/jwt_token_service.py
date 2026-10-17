"""Emision de tokens JWT sin estado (implementacion de infraestructura)."""

import os
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.domain.services.token_service import TokenService

# Algoritmo simetrico (el secreto nunca se escribe en el codigo).
_ALGORITHM = "HS256"
# Vigencia por defecto del token.
_DEFAULT_EXPIRES_MINUTES = 30


class JwtTokenService(TokenService):
    """Implementa TokenService con python-jose (incluye el rol en el token)."""

    def __init__(
        self, secret_key: str | None = None,
        expires_minutes: int = _DEFAULT_EXPIRES_MINUTES
    ) -> None:

        """Lee el secreto del entorno salvo que se inyecte (util para pruebas)."""

        # key: almacena la SECRET_KEY.
        key = secret_key if secret_key is not None else os.getenv("SECRET_KEY", "")
        if not key:
            raise ValueError("SECRET_KEY is required.")
        self._secret_key = key
        self._expires_minutes = expires_minutes

    def issue_token(self, user_id: str, username: str, role: str) -> str:
        """Emite un JWT con sub, username, rol y expiracion."""

        # Obtiene la fecha y hora actual con timezone UTC y la almacena en now.
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "iat": now,
            "exp": now + timedelta(minutes=self._expires_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=_ALGORITHM)
