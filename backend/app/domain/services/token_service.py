"""Contrato del servicio de tokens (inversion de dependencias)."""

from abc import ABC, abstractmethod


class TokenService(ABC):
    """Emite tokens de sesion sin estado con la identidad y el rol."""

    @abstractmethod
    def issue_token(self, user_id: str, username: str, role: str) -> str:
        """Emite un token firmado con la identidad y el rol."""
        raise NotImplementedError
