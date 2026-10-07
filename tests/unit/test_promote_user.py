"""Pruebas unitarias del caso de uso PromoteUser."""

from typing import Dict, Optional, Tuple

import pytest

from app.application.use_cases.user.promote_user import PromoteUser
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    ForbiddenException,
    UserNotFoundException,
    UserValidationException,
)
from app.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    """Repositorio falso en memoria para las pruebas."""

    def __init__(self) -> None:
        """Inicializa los indices por id, username y correo normalizado."""
        self._by_id: Dict[int, User] = {}
        self._by_username: Dict[str, User] = {}
        self._by_email: Dict[str, User] = {}

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca por id."""
        return self._by_id.get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca por username exacto."""
        return self._by_username.get(username)

    def get_by_email_normalized(self, email_normalized: str) -> Optional[User]:
        """Busca por correo normalizado."""
        return self._by_email.get(email_normalized)

    def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Resuelve por @ como correo o como username exacto."""
        if "@" in identifier:
            return self.get_by_email_normalized(identifier.strip().lower())
        return self.get_by_username(identifier)

    def save(self, user: User) -> User:
        """Guarda indexando por id, username y correo normalizado."""
        assert user.id is not None
        self._by_id[user.id] = user
        self._by_username[user.username] = user
        self._by_email[user.email.lower()] = user
        return user

    def update(self, user: User) -> User:
        """Actualiza el usuario existente."""
        assert user.id is not None
        self._by_id[user.id] = user
        self._by_username[user.username] = user
        self._by_email[user.email.lower()] = user
        return user


def make_promote() -> Tuple[PromoteUser, InMemoryUserRepository]:
    """Crea el caso de uso con un ADMIN (id 1) y un USER (id 2)."""
    repository = InMemoryUserRepository()
    repository.save(
        User(
            id=1,
            username="adminuser01",
            email="admin@mail.com",
            password_hash="hashed",
            role="ADMIN",
        )
    )
    repository.save(
        User(
            id=2,
            username="validuser01",
            email="user@mail.com",
            password_hash="hashed",
            role="USER",
        )
    )
    return PromoteUser(repository=repository), repository


def test_admin_promotion_succeeds():
    """Un ADMIN otorga ADMIN a un USER existente."""
    use_case, repository = make_promote()
    admin = repository.get_by_id(1)
    assert admin is not None

    output = use_case.execute(requester=admin, target_user_id=2, new_role="ADMIN")

    assert output.role == "ADMIN"
    assert output.username == "validuser01"
    target = repository.get_by_id(2)
    assert target is not None
    assert target.role == "ADMIN"


def test_non_admin_yields_forbidden_without_changes():
    """Un USER no puede otorgar ADMIN (el objetivo no cambia)."""
    use_case, repository = make_promote()
    plain = repository.get_by_id(2)
    assert plain is not None

    with pytest.raises(ForbiddenException):
        use_case.execute(requester=plain, target_user_id=2, new_role="ADMIN")

    target = repository.get_by_id(2)
    assert target is not None
    assert target.role == "USER"


def test_missing_target_yields_not_found():
    """Promocionar un usuario inexistente da no-encontrado."""
    use_case, repository = make_promote()
    admin = repository.get_by_id(1)
    assert admin is not None

    with pytest.raises(UserNotFoundException):
        use_case.execute(requester=admin, target_user_id=999, new_role="ADMIN")


def test_invalid_role_yields_validation_without_changes():
    """Roles distintos de ADMIN se rechazan (el objetivo no cambia)."""
    use_case, repository = make_promote()
    admin = repository.get_by_id(1)
    assert admin is not None

    for bad_role in ("USER", "SUPER", ""):
        with pytest.raises(UserValidationException):
            use_case.execute(
                requester=admin, target_user_id=2, new_role=bad_role
            )

    target = repository.get_by_id(2)
    assert target is not None
    assert target.role == "USER"
