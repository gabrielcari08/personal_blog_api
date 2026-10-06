"""Contrato del servicio de hash de claves."""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Define el hash y la verificacion sin atarse a una libreria."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Genera el hash de una clave en texto plano."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Compara la clave en plano contra el hash en tiempo constante."""
        raise NotImplementedError
