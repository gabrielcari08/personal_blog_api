"""Contrato del repositorio de usuarios (inversion de dependencias)."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user import User


class UserRepository(ABC):
    """Define la persistencia de usuarios sin depender de infraestructura."""

    # Metodos de consulta (get_by...)
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por su identificador opaco."""
        raise NotImplementedError

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Busca por username con comparacion exacta (sensible a mayusculas)."""
        raise NotImplementedError

    @abstractmethod
    def get_by_email_normalized(self, email_normalized: str) -> Optional[User]:
        """Busca por correo ya normalizado (recortado y en minusculas)."""
        raise NotImplementedError

    @abstractmethod
    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Resuelve login: con @ va por correo (recorte+minusculas), si no por username exacto."""
        raise NotImplementedError

    # Metodos de persistencia y modificación.
    @abstractmethod
    def save(self, user: User) -> User:
        """Guarda un usuario nuevo y lo devuelve."""
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario existente (p. ej. cambio de rol) y lo devuelve."""
        raise NotImplementedError
