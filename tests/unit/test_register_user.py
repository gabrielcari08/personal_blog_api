"""Pruebas unitarias del caso de uso RegisterUser."""

from typing import Dict, Optional

import pytest

from app.application.dtos.user_dtos import RegisterInput
from app.application.use_cases.user.register_user import RegisterUser
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    UserValidationException,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher_service import PasswordHasher


class InMemoryUserRepository(UserRepository):
    """Repositorio falso en memoria para las pruebas."""

    def __init__(self) -> None:
        """Inicializa los indices por id, username y correo normalizado."""
        self._by_id: Dict[str, User] = {}
        self._by_username: Dict[str, User] = {}
        self._by_email: Dict[str, User] = {}

    def get_by_id(self, user_id: str) -> Optional[User]:
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


def make_use_case() -> RegisterUser:
    """Crea el caso de uso con dobles falsos."""
    return RegisterUser(repository=InMemoryUserRepository(), hasher=FakeHasher())


def test_success_returns_user_without_token():
    """El registro exitoso devuelve USER y ningun token."""
    use_case = make_use_case()

    output = use_case.execute(
        RegisterInput(
            username="validuser01",
            email="user@mail.com",
            password="password12",
        )
    )

    assert output.role == "USER"
    assert output.username == "validuser01"
    assert output.email == "user@mail.com"
    assert "token" not in output.model_dump()


def test_client_role_is_ignored():
    """Un rol ADMIN enviado por el cliente se ignora y queda USER."""
    use_case = make_use_case()

    output = use_case.execute(
        RegisterInput(
            username="validuser01",
            email="user@mail.com",
            password="password12",
            role="ADMIN",  # type: ignore[call-arg]
        )
    )

    assert output.role == "USER"


def test_email_with_spaces_is_trimmed():
    """El correo con espacios se recorta antes de guardar."""
    use_case = make_use_case()

    output = use_case.execute(
        RegisterInput(
            username="validuser01",
            email="  user@mail.com  ",
            password="password12",
        )
    )

    assert output.email == "user@mail.com"


def test_duplicate_username_exact_case_fails():
    """El username duplicado exacto se rechaza."""
    use_case = make_use_case()
    data = RegisterInput(
        username="validuser01", email="first@mail.com", password="password12"
    )
    use_case.execute(data)

    with pytest.raises(DuplicateUsernameException):
        use_case.execute(
            RegisterInput(
                username="validuser01",
                email="second@mail.com",
                password="password12",
            )
        )


def test_duplicate_username_different_case_succeeds():
    """El username con distinta capitalizacion se acepta (sensible a mayusculas)."""
    use_case = make_use_case()
    use_case.execute(
        RegisterInput(
            username="Validuser01", email="first@mail.com", password="password12"
        )
    )

    output = use_case.execute(
        RegisterInput(
            username="validuser01",
            email="second@mail.com",
            password="password12",
        )
    )

    assert output.username == "validuser01"


def test_duplicate_email_same_and_different_case_fail():
    """El correo duplicado se rechaza sin importar las mayusculas."""
    use_case = make_use_case()
    use_case.execute(
        RegisterInput(
            username="validuser01", email="User@mail.com", password="password12"
        )
    )

    with pytest.raises(DuplicateEmailException):
        use_case.execute(
            RegisterInput(
                username="validuser02",
                email="User@mail.com",
                password="password12",
            )
        )

    with pytest.raises(DuplicateEmailException):
        use_case.execute(
            RegisterInput(
                username="validuser03",
                email="user@MAIL.com",
                password="password12",
            )
        )


def test_username_boundaries():
    """Username de 7 y 21 falla; 8 y 20 pasan."""
    use_case = make_use_case()

    with pytest.raises(UserValidationException):
        use_case.execute(
            RegisterInput(
                username="u" * 7, email="a1@mail.com", password="password12"
            )
        )

    use_case.execute(
        RegisterInput(username="u" * 8, email="a2@mail.com", password="password12")
    )
    use_case.execute(
        RegisterInput(username="u" * 20, email="a3@mail.com", password="password12")
    )

    with pytest.raises(UserValidationException):
        use_case.execute(
            RegisterInput(
                username="u" * 21, email="a4@mail.com", password="password12"
            )
        )


def test_password_boundaries():
    """Clave de 7 y 21 falla; 8 y 20 pasan."""
    use_case = make_use_case()

    with pytest.raises(UserValidationException):
        use_case.execute(
            RegisterInput(
                username="validuser01", email="a1@mail.com", password="a" * 7
            )
        )

    use_case.execute(
        RegisterInput(username="validuser02", email="a2@mail.com", password="a" * 8)
    )
    use_case.execute(
        RegisterInput(username="validuser03", email="a3@mail.com", password="a" * 20)
    )

    with pytest.raises(UserValidationException):
        use_case.execute(
            RegisterInput(
                username="validuser04", email="a4@mail.com", password="a" * 21
            )
        )


def test_username_with_spaces_rejected():
    """Usernames con blancos se rechazan sin recortar."""
    use_case = make_use_case()

    for bad in ("my user01", " user01AB", "user01AB "):
        with pytest.raises(UserValidationException):
            use_case.execute(
                RegisterInput(
                    username=bad, email="user@mail.com", password="password12"
                )
            )
