"""Repositorio de usuarios en PostgreSQL (implementacion de infraestructura)."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    UserNotFoundException,
)
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.db.models.user_model import UserModel


class PostgresUserRepository(UserRepository):
    """Implementa UserRepository con SQLAlchemy sobre PostgreSQL."""

    def __init__(self, session: Session) -> None:
        """Guarda la sesion SQLAlchemy inyectada."""
        self._session = session

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por su id."""
        model = self._session.get(UserModel, user_id)
        return self._to_entity(model) if model is not None else None

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca por username con comparacion exacta (sensible a mayusculas)."""
        model = (
            self._session.query(UserModel)
            .filter(UserModel.username == username)
            .first()
        )
        return self._to_entity(model) if model is not None else None

    def get_by_email_normalized(self, email_normalized: str) -> Optional[User]:
        """Busca por correo normalizado (el llamante lo pasa en minusculas)."""
        model = (
            self._session.query(UserModel)
            .filter(UserModel.email_normalized == email_normalized)
            .first()
        )
        return self._to_entity(model) if model is not None else None

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Resuelve login: con @ va por correo (recorte+minusculas), si no exacto."""
        if "@" in identifier:
            return self.get_by_email_normalized(identifier.strip().lower())
        return self.get_by_username(identifier)

    def save(self, user: User) -> User:
        """Guarda un usuario nuevo (traduce UNIQUE a excepciones de dominio)."""
        model = UserModel(
            username=user.username,
            email=user.email.strip(),
            email_normalized=user.email.strip().lower(),
            password_hash=user.password_hash,
            role=user.role,
        )
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise self._map_unique_violation(error) from error
        self._session.refresh(model)
        return self._to_entity(model)

    def update(self, user: User) -> User:
        """Actualiza un usuario existente (p. ej. cambio de rol)."""
        model = self._session.get(UserModel, user.id)
        if model is None:
            raise UserNotFoundException("User not found.")
        model.username = user.username
        model.email = user.email.strip()
        model.email_normalized = user.email.strip().lower()
        model.password_hash = user.password_hash
        model.role = user.role
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise self._map_unique_violation(error) from error
        self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """Convierte una fila ORM en entidad de dominio."""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            created_at=model.created_at,
        )

    @staticmethod
    def _map_unique_violation(error: IntegrityError) -> Exception:
        """Traduce la restriccion violada a la excepcion de dominio adecuada."""
        name = getattr(getattr(error, "orig", None), "diag", None)
        constraint = getattr(name, "constraint_name", "") or ""
        if "email_normalized" in constraint:
            return DuplicateEmailException("Email already registered.")
        return DuplicateUsernameException("Username already registered.")
