"""Pruebas e2e del login HTTP (POST /api/v1/users/login)."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.user import User
from app.entrypoints.api.main import app
from app.entrypoints.api.v1.dependencies import get_db
from app.infrastructure.db.base import Base
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/blog_test",
)
# Secreto solo para las pruebas.
TEST_SECRET = "test-secret-key"

engine = create_engine(TEST_URL)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def _override_db() -> Generator[Session, None, None]:
    """Entrega sesiones de prueba en lugar de la base de desarrollo."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Configura el secreto y limpia la tabla users por prueba."""
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    session = TestingSession()
    session.execute(text("TRUNCATE users RESTART IDENTITY"))
    session.commit()
    session.close()
    yield
    session = TestingSession()
    session.execute(text("TRUNCATE users RESTART IDENTITY"))
    session.commit()
    session.close()


def _create_user(
    username: str = "loginuser01",
    email: str = "User@mail.com",
    password: str = "password12",
    role: str = "USER",
) -> None:
    """Crea un usuario directo en la base de pruebas."""
    session = TestingSession()
    try:
        repository = PostgresUserRepository(session)
        repository.save(
            User(
                username=username,
                email=email,
                password_hash=BcryptPasswordHasher().hash(password),
                role=role,  # type: ignore[arg-type]
            )
        )
    finally:
        session.close()


def test_login_via_email_returns_200_with_role_token():
    """El login con email devuelve token con el rol correcto."""
    _create_user()

    response = client.post(
        "/api/v1/users/login",
        json={"identifier": "User@mail.com", "password": "password12"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], TEST_SECRET, algorithms=["HS256"])
    assert claims["username"] == "loginuser01"
    assert claims["role"] == "USER"


def test_login_via_username_returns_200():
    """El login con username exacto devuelve token."""
    _create_user()

    response = client.post(
        "/api/v1/users/login",
        json={"identifier": "loginuser01", "password": "password12"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_via_differently_cased_email_returns_200():
    """El login con el correo en otras mayusculas tambien funciona."""
    _create_user()

    response = client.post(
        "/api/v1/users/login",
        json={"identifier": "user@MAIL.com", "password": "password12"},
    )

    assert response.status_code == 200


def test_wrong_password_and_unknown_user_share_body():
    """Clave erronea e identificador inexistente dan el mismo 401."""
    _create_user()

    wrong_password = client.post(
        "/api/v1/users/login",
        json={"identifier": "loginuser01", "password": "wrongpass12"},
    )
    unknown_user = client.post(
        "/api/v1/users/login",
        json={"identifier": "nouser9999", "password": "password12"},
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_missing_fields_return_400():
    """Campos ausentes o vacios dan 400."""
    assert client.post("/api/v1/users/login", json={}).status_code == 400

    response = client.post(
        "/api/v1/users/login", json={"identifier": "loginuser01"}
    )
    assert response.status_code == 400

    response = client.post(
        "/api/v1/users/login", json={"identifier": "", "password": "password12"}
    )
    assert response.status_code == 400
