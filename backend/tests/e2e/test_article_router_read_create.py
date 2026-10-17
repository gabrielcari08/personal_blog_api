"""Pruebas e2e de lectura publica y creacion HTTP de articulos."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
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
    """Configura el secreto y limpia las tablas por prueba."""
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    session = TestingSession()
    session.execute(text("TRUNCATE articles, users RESTART IDENTITY"))
    session.commit()
    session.close()
    yield
    session = TestingSession()
    session.execute(text("TRUNCATE articles, users RESTART IDENTITY"))
    session.commit()
    session.close()


def _create_user(
    username: str = "authoruser01",
    email: str = "author@mail.com",
    password: str = "password12",
    role: str = "USER",
) -> None:
    """Crea un usuario directo en la base de pruebas."""
    session = TestingSession()
    try:
        PostgresUserRepository(session).save(
            User(
                username=username,
                email=email,
                password_hash=BcryptPasswordHasher().hash(password),
                role=role,  # type: ignore[arg-type]
            )
        )
    finally:
        session.close()


def _token(identifier: str = "authoruser01", password: str = "password12") -> str:
    """Autentica por HTTP y devuelve el token de acceso."""
    response = client.post(
        "/api/v1/users/login", json={"identifier": identifier, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth() -> dict:
    """Crea el autor, autentica y devuelve la cabecera Bearer."""
    _create_user()
    return {"Authorization": f"Bearer {_token()}"}


def _payload(**overrides: object) -> dict:
    """Construye un cuerpo valido para crear un articulo."""
    data: dict = {"title": "Valid Titl", "text": "This is a valid text."}
    data.update(overrides)
    return data


def test_public_list_empty_without_token():
    """El listado publico sin token devuelve vacio."""
    response = client.get("/api/v1/articles")

    assert response.status_code == 200
    assert response.json() == []


def test_create_returns_201_with_owner_and_time():
    """Crear con token devuelve el articulo con autor y tiempo del servidor."""
    headers = _auth()

    response = client.post("/api/v1/articles", json=_payload(), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Valid Titl"
    assert body["text"] == "This is a valid text."
    assert body["user_id"] == 1
    assert body["created_at"] is not None
    assert body["id"] is not None


def test_created_article_immediately_visible_in_public_list():
    """Lo creado aparece de inmediato en la lectura publica ordenada."""
    headers = _auth()
    client.post("/api/v1/articles", json=_payload(title="First Arti"), headers=headers)
    client.post("/api/v1/articles", json=_payload(title="Second Art"), headers=headers)

    response = client.get("/api/v1/articles")

    assert response.status_code == 200
    listed = response.json()
    assert [item["title"] for item in listed] == ["Second Art", "First Arti"]
    assert all(item["user_id"] == 1 for item in listed)


def test_public_single_returns_article_without_token():
    """El detalle publico sin token incluye autor y tiempo."""
    headers = _auth()
    created = client.post("/api/v1/articles", json=_payload(), headers=headers)
    article_id = created.json()["id"]

    response = client.get(f"/api/v1/articles/{article_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Valid Titl"
    assert body["user_id"] == 1
    assert body["created_at"] is not None


def test_public_single_missing_returns_404():
    """El detalle de un id inexistente da 404 con su codigo."""
    response = client.get("/api/v1/articles/999999")

    assert response.status_code == 404
    assert response.json()["code"] == "article_not_found"


def test_create_without_token_returns_401():
    """Crear sin token se rechaza sin guardar nada."""
    response = client.post("/api/v1/articles", json=_payload())

    assert response.status_code == 401
    assert client.get("/api/v1/articles").json() == []


def test_short_and_long_title_return_400_with_exact_message():
    """Titulos de 7 y 21 caracteres dan 400 con el mensaje exacto."""
    headers = _auth()

    short = client.post(
        "/api/v1/articles", json=_payload(title="t" * 7), headers=headers
    )
    long = client.post(
        "/api/v1/articles", json=_payload(title="t" * 21), headers=headers
    )

    assert short.status_code == 400
    assert short.json()["detail"] == "title must be 8-20 characters."
    assert long.status_code == 400
    assert long.json()["detail"] == "title must be 8-20 characters."
    assert client.get("/api/v1/articles").json() == []


def test_empty_text_returns_400_with_required_message():
    """Texto vacio da 400 con el mensaje de requerido."""
    headers = _auth()

    response = client.post(
        "/api/v1/articles", json=_payload(text=""), headers=headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "text is required."


def test_short_and_long_text_return_400_with_range_message():
    """Textos de 9 y 301 caracteres dan 400 con el mensaje de rango."""
    headers = _auth()

    short = client.post(
        "/api/v1/articles", json=_payload(text="x" * 9), headers=headers
    )
    long = client.post(
        "/api/v1/articles", json=_payload(text="x" * 301), headers=headers
    )

    assert short.status_code == 400
    assert short.json()["detail"] == "text must be 10-300 characters."
    assert long.status_code == 400
    assert long.json()["detail"] == "text must be 10-300 characters."


def test_client_author_and_time_are_ignored():
    """El cuerpo no puede imponer autor ni tiempo."""
    headers = _auth()

    response = client.post(
        "/api/v1/articles",
        json=_payload(user_id=999, created_at="2020-01-01T00:00:00+00:00"),
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == 1
    assert not body["created_at"].startswith("2020")


def test_missing_fields_return_400():
    """Cuerpos sin titulo o sin texto dan 400."""
    headers = _auth()

    assert client.post("/api/v1/articles", json={}, headers=headers).status_code == 400
    assert (
        client.post(
            "/api/v1/articles", json={"text": "This is a valid text."}, headers=headers
        ).status_code
        == 400
    )
