"""Pruebas e2e de edicion y eliminacion HTTP de articulos."""

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
    username: str,
    email: str,
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


def _token(identifier: str, password: str = "password12") -> str:
    """Autentica por HTTP y devuelve el token de acceso."""
    response = client.post(
        "/api/v1/users/login", json={"identifier": identifier, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _setup() -> dict:
    """Crea autor, otro USER y ADMIN; devuelve sus cabeceras Bearer."""
    _create_user("authoruser01", "author@mail.com")
    _create_user("otheruser01", "other@mail.com")
    _create_user("adminuser01", "admin@mail.com", role="ADMIN")
    return {
        "author": {"Authorization": f"Bearer {_token('authoruser01')}"},
        "other": {"Authorization": f"Bearer {_token('otheruser01')}"},
        "admin": {"Authorization": f"Bearer {_token('adminuser01')}"},
    }


def _create(headers: dict, title: str = "Original T") -> dict:
    """Crea un articulo por HTTP y devuelve su cuerpo."""
    response = client.post(
        "/api/v1/articles",
        json={"title": title, "text": "Original text here."},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_owner_put_returns_200_preserving_history():
    """El autor edita y conserva autor y tiempo originales."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "Edited Tit", "text": "This text was edited."},
        headers=headers["author"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Edited Tit"
    assert body["text"] == "This text was edited."
    assert body["user_id"] == created["user_id"]
    assert body["created_at"] == created["created_at"]


def test_owner_put_invalid_keeps_originals():
    """Valores nuevos invalidos dan 400 exacto sin cambiar nada."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "short", "text": "This text was edited."},
        headers=headers["author"],
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "title must be 8-20 characters."
    assert client.get(f"/api/v1/articles/{created['id']}").json()["title"] == (
        "Original T"
    )


def test_non_owner_put_returns_403_without_changes():
    """El intento directo de un USER ajeno da 403 aunque oculte botones."""
    headers = _setup()
    created = _create(headers["author"])
    # La lectura publica expone el autor para que el cliente oculte acciones.
    assert client.get(f"/api/v1/articles/{created['id']}").json()["user_id"] != 2

    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "Hacked Tit", "text": "Hacked text here!"},
        headers=headers["other"],
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    assert client.get(f"/api/v1/articles/{created['id']}").json()["title"] == (
        "Original T"
    )


def test_non_owner_delete_returns_403_without_removing():
    """El borrado directo de un USER ajeno da 403 sin borrar nada."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.delete(
        f"/api/v1/articles/{created['id']}", headers=headers["other"]
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    assert client.get(f"/api/v1/articles/{created['id']}").status_code == 200


def test_admin_put_of_other_article_succeeds():
    """Un ADMIN edita el articulo ajeno sin cambiar su historia."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "Moderated T", "text": "Moderated text here."},
        headers=headers["admin"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Moderated T"
    assert body["user_id"] == created["user_id"]
    assert body["created_at"] == created["created_at"]


def test_admin_delete_of_other_article_returns_204():
    """Un ADMIN borra el articulo ajeno y desaparece de la lectura."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.delete(
        f"/api/v1/articles/{created['id']}", headers=headers["admin"]
    )

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/articles/{created['id']}").status_code == 404
    assert client.get("/api/v1/articles").json() == []


def test_owner_delete_returns_204_and_vanishes():
    """El autor borra con 204 vacio y el articulo ya no se ve."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.delete(
        f"/api/v1/articles/{created['id']}", headers=headers["author"]
    )

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/articles/{created['id']}").status_code == 404
    assert client.get("/api/v1/articles").json() == []


def test_put_and_delete_missing_return_404():
    """Editar o borrar un id inexistente da 404 con su codigo."""
    headers = _setup()

    put = client.put(
        "/api/v1/articles/999999",
        json={"title": "Edited Tit", "text": "This text was edited."},
        headers=headers["author"],
    )
    delete = client.delete("/api/v1/articles/999999", headers=headers["author"])

    assert put.status_code == 404
    assert put.json()["code"] == "article_not_found"
    assert delete.status_code == 404
    assert delete.json()["code"] == "article_not_found"


def test_put_and_delete_without_token_return_401():
    """Sin token, editar y borrar se rechazan sin cambiar nada."""
    headers = _setup()
    created = _create(headers["author"])

    put = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "Edited Tit", "text": "This text was edited."},
    )
    delete = client.delete(f"/api/v1/articles/{created['id']}")

    assert put.status_code == 401
    assert delete.status_code == 401
    assert client.get(f"/api/v1/articles/{created['id']}").json()["title"] == (
        "Original T"
    )


def test_put_missing_fields_return_400():
    """La edicion exige titulo y texto completos."""
    headers = _setup()
    created = _create(headers["author"])

    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "Edited Tit"},
        headers=headers["author"],
    )

    assert response.status_code == 400
