"""Pruebas e2e del registro HTTP (POST /api/v1/users/register)."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.entrypoints.api.main import app
from app.entrypoints.api.v1.dependencies import get_db
from app.infrastructure.db.base import Base

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blog_test",
)

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
def _clean() -> Generator[None, None, None]:
    """Limpia la tabla users despues de cada prueba."""
    yield
    session = TestingSession()
    session.execute(text("TRUNCATE users RESTART IDENTITY"))
    session.commit()
    session.close()


def _payload(**overrides: object) -> dict:
    """Construye un cuerpo valido para el registro."""
    data: dict = {
        "username": "testuser01",
        "email": "user@mail.com",
        "password": "password12",
    }
    data.update(overrides)
    return data


def test_success_returns_201_user_without_token():
    """El registro exitoso crea USER e indica ir al login."""
    response = client.post("/api/v1/users/register", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "USER"
    assert body["username"] == "testuser01"
    assert body["email"] == "user@mail.com"
    assert "log in" in body["message"].lower()
    assert "token" not in response.text.lower()


def test_client_role_is_ignored():
    """Un rol ADMIN en el cuerpo se ignora y queda USER."""
    response = client.post("/api/v1/users/register", json=_payload(role="ADMIN"))

    assert response.status_code == 201
    assert response.json()["role"] == "USER"


def test_duplicate_username_returns_409():
    """El username repetido exacto da 409 con su codigo."""
    client.post("/api/v1/users/register", json=_payload(email="first@mail.com"))

    response = client.post(
        "/api/v1/users/register", json=_payload(email="second@mail.com")
    )

    assert response.status_code == 409
    assert response.json()["code"] == "duplicate_username"


def test_duplicate_username_different_case_succeeds():
    """El username con otras mayusculas no duplica (sensible a caso)."""
    client.post(
        "/api/v1/users/register",
        json=_payload(username="Testuser01", email="first@mail.com"),
    )

    response = client.post(
        "/api/v1/users/register",
        json=_payload(username="testuser01", email="second@mail.com"),
    )

    assert response.status_code == 201


def test_duplicate_email_different_case_returns_409():
    """El correo repetido con otras mayusculas da 409 con su codigo."""
    client.post(
        "/api/v1/users/register",
        json=_payload(username="testuser01", email="User@mail.com"),
    )

    response = client.post(
        "/api/v1/users/register",
        json=_payload(username="testuser02", email="user@MAIL.com"),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "duplicate_email"


def test_bad_email_returns_400():
    """El correo con formato invalido da 400."""
    response = client.post("/api/v1/users/register", json=_payload(email="bad"))

    assert response.status_code == 400


def test_short_and_long_username_return_400():
    """Usernames de 7 y 21 caracteres dan 400."""
    short = client.post("/api/v1/users/register", json=_payload(username="u" * 7))
    long = client.post("/api/v1/users/register", json=_payload(username="u" * 21))

    assert short.status_code == 400
    assert long.status_code == 400


def test_username_with_spaces_returns_400():
    """Usernames con blancos (incluidos extremos) dan 400."""
    for bad in ("my user01", " testuser01", "testuser01 "):
        response = client.post(
            "/api/v1/users/register", json=_payload(username=bad)
        )

        assert response.status_code == 400


def test_short_and_long_password_return_400():
    """Claves de 7 y 21 caracteres dan 400."""
    short = client.post("/api/v1/users/register", json=_payload(password="a" * 7))
    long = client.post("/api/v1/users/register", json=_payload(password="a" * 21))

    assert short.status_code == 400
    assert long.status_code == 400


def test_missing_fields_return_400():
    """Campos ausentes o vacios dan 400."""
    assert client.post("/api/v1/users/register", json={}).status_code == 400

    payload = _payload()
    del payload["password"]
    assert client.post("/api/v1/users/register", json=payload).status_code == 400

    payload = _payload()
    del payload["username"]
    assert client.post("/api/v1/users/register", json=payload).status_code == 400

    assert (
        client.post("/api/v1/users/register", json=_payload(email="   ")).status_code
        == 400
    )
