"""Pruebas de integracion del repositorio Postgres."""

import os
from dataclasses import replace
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    UserNotFoundException,
)
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blog_test",
)

engine = create_engine(TEST_URL)
TestingSession = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def _tables() -> Generator[None, None, None]:
    """Crea las tablas una vez para todo el modulo."""
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def repository() -> Generator[PostgresUserRepository, None, None]:
    """Entrega un repositorio con sesion limpia por prueba."""
    session: Session = TestingSession()
    yield PostgresUserRepository(session)
    session.execute(text("TRUNCATE users RESTART IDENTITY"))
    session.commit()
    session.close()


def _user(**overrides: object) -> User:
    """Construye un usuario valido con valores por defecto."""
    data = {
        "username": "validuser01",
        "email": "user@mail.com",
        "password_hash": "hashed",
        "role": "USER",
    }
    data.update(overrides)  # type: ignore[typeddict-item]
    return User(**data)  # type: ignore[arg-type]


def test_round_trip_persists_all_fields(repository: PostgresUserRepository):
    """Guardar y leer devuelve los mismos datos incluido el rol."""
    saved = repository.save(_user())

    assert saved.id is not None
    found = repository.get_by_id(saved.id)
    assert found is not None
    assert found.username == "validuser01"
    assert found.email == "user@mail.com"
    assert found.password_hash == "hashed"
    assert found.role == "USER"
    assert found.created_at is not None


def test_username_lookup_is_case_sensitive(repository: PostgresUserRepository):
    """El username exacto se encuentra; con otras mayusculas no."""
    repository.save(_user(username="User01AB"))

    assert repository.get_by_username("User01AB") is not None
    assert repository.get_by_username("user01ab") is None


def test_email_lookup_is_case_insensitive(repository: PostgresUserRepository):
    """El correo se encuentra en minusculas conservando su presentacion."""
    repository.save(_user(email="User@mail.com"))

    found = repository.get_by_email_normalized("user@mail.com")
    assert found is not None
    assert found.email == "User@mail.com"


def test_duplicate_username_raises(repository: PostgresUserRepository):
    """Guardar un username repetido da error de dominio."""
    repository.save(_user(username="validuser01", email="first@mail.com"))

    with pytest.raises(DuplicateUsernameException):
        repository.save(_user(username="validuser01", email="second@mail.com"))


def test_duplicate_email_different_case_raises(repository: PostgresUserRepository):
    """Guardar un correo repetido con otras mayusculas da error de dominio."""
    repository.save(_user(username="validuser01", email="User@mail.com"))

    with pytest.raises(DuplicateEmailException):
        repository.save(_user(username="validuser02", email="user@MAIL.com"))


def test_stored_email_is_trimmed(repository: PostgresUserRepository):
    """El correo guardado queda recortado y normalizado."""
    saved = repository.save(_user(email="  user@mail.com  "))
    assert saved.id is not None

    found = repository.get_by_id(saved.id)
    assert found is not None
    assert found.email == "user@mail.com"
    assert repository.get_by_email_normalized("user@mail.com") is not None


def test_update_role_keeps_other_fields(repository: PostgresUserRepository):
    """Actualizar el rol no altera los demas campos."""
    saved = repository.save(_user())
    assert saved.id is not None

    updated = repository.update(replace(saved, role="ADMIN"))

    assert updated.role == "ADMIN"
    found = repository.get_by_id(saved.id)
    assert found is not None
    assert found.role == "ADMIN"
    assert found.username == saved.username
    assert found.email == saved.email
    assert found.password_hash == saved.password_hash


def test_update_missing_raises_not_found(repository: PostgresUserRepository):
    """Actualizar un usuario inexistente da no-encontrado."""
    ghost = User(
        id=999999,
        username="ghostuser01",
        email="ghost@mail.com",
        password_hash="hashed",
        role="ADMIN",
    )

    with pytest.raises(UserNotFoundException):
        repository.update(ghost)


def test_get_by_identifier_routing(repository: PostgresUserRepository):
    """El identificador con @ va por correo; si no, por username exacto."""
    repository.save(_user(username="validuser01", email="User@mail.com"))

    assert repository.get_by_identifier("  USER@mail.com  ") is not None
    assert repository.get_by_identifier("validuser01") is not None
    assert repository.get_by_identifier(" validuser01 ") is None
    assert repository.get_by_identifier("nouser9999") is None
