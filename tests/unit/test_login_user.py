"""Pruebas unitarias del caso de uso LoginUser."""

from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import pytest
from pydantic import ValidationError

from app.application.dtos.user_dtos import LoginInput
from app.application.use_cases.user.login_user import LoginUser
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    InvalidCredentialsException,
    UserValidationException,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher_service import PasswordHasher


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


class FakeHasher(PasswordHasher):
    """Cifrador falso determinista para las pruebas."""

    def hash(self, plain_password: str) -> str:
        """Devuelve un hash simulado con prefijo."""
        return "hashed:" + plain_password

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verifica comparando contra el formato simulado."""
        return password_hash == "hashed:" + plain_password


class FakeTokens:
    """Servicio de tokens falso que registra las emisiones."""

    def __init__(self) -> None:
        """Inicializa el registro de llamadas."""
        self.calls: List[Tuple[str, str, str]] = []

    def issue_token(self, user_id: str, username: str, role: str) -> str:
        """Registra la llamada y devuelve un token simulado."""
        self.calls.append((user_id, username, role))
        return "token:" + user_id + ":" + role


def make_login() -> Tuple[LoginUser, FakeTokens]:
    """Crea el caso de uso con un usuario USER y uno ADMIN precargados."""
    repository = InMemoryUserRepository()
    hasher = FakeHasher()
    tokens = FakeTokens()
    repository.save(
        User(
            id=1,
            username="validuser01",
            email="User@mail.com",
            password_hash=hasher.hash("password12"),
            role="USER",
        )
    )
    repository.save(
        User(
            id=2,
            username="adminuser01",
            email="admin@mail.com",
            password_hash=hasher.hash("password12"),
            role="ADMIN",
        )
    )
    return LoginUser(repository=repository, hasher=hasher, tokens=tokens), tokens


def test_login_via_email_succeeds_with_role():
    """El login con email devuelve token y registra el rol USER."""
    use_case, tokens = make_login()

    output = use_case.execute(
        LoginInput(identifier="User@mail.com", password="password12")
    )

    assert output.access_token.startswith("token:")
    assert output.token_type == "bearer"
    assert tokens.calls[-1] == ("1", "validuser01", "USER")


def test_login_via_username_succeeds():
    """El login con username exacto devuelve token."""
    use_case, _ = make_login()

    output = use_case.execute(
        LoginInput(identifier="validuser01", password="password12")
    )

    assert output.access_token.startswith("token:")


def test_login_via_differently_cased_email_succeeds():
    """El login con el correo en otras mayusculas tambien funciona."""
    use_case, _ = make_login()

    output = use_case.execute(
        LoginInput(identifier="user@MAIL.com", password="password12")
    )

    assert output.access_token.startswith("token:")


def test_login_admin_carries_admin_role():
    """El token del administrador lleva el rol ADMIN."""
    use_case, tokens = make_login()

    use_case.execute(LoginInput(identifier="adminuser01", password="password12"))

    assert tokens.calls[-1] == ("2", "adminuser01", "ADMIN")


def test_wrong_password_and_unknown_user_raise_identical_error():
    """Clave erronea y usuario inexistente dan el mismo tipo y mensaje."""
    use_case, _ = make_login()

    with pytest.raises(InvalidCredentialsException) as wrong_password:
        use_case.execute(
            LoginInput(identifier="validuser01", password="wrongpass12")
        )

    with pytest.raises(InvalidCredentialsException) as unknown_user:
        use_case.execute(
            LoginInput(identifier="nouser9999", password="password12")
        )

    assert type(wrong_password.value) is type(unknown_user.value)
    assert str(wrong_password.value) == str(unknown_user.value)


def test_empty_identifier_and_password_raise_validation():
    """Identificador o clave vacios dan error de validacion, no de credenciales."""
    # Nivel DTO: Pydantic rechaza los vacios antes del caso de uso.
    with pytest.raises(ValidationError):
        LoginInput(identifier="", password="password12")

    with pytest.raises(ValidationError):
        LoginInput(identifier="validuser01", password="")

    # Nivel caso de uso: guardia defensiva con el mismo tipo de error.
    use_case, _ = make_login()
    with pytest.raises(UserValidationException):
        use_case.execute(SimpleNamespace(identifier="", password="password12"))

    with pytest.raises(UserValidationException):
        use_case.execute(SimpleNamespace(identifier="validuser01", password=""))


def test_username_with_spaces_does_not_match():
    """El identifier con espacios no se recorta y no autentica como username."""
    use_case, _ = make_login()

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(
            LoginInput(identifier=" validuser01 ", password="password12")
        )
