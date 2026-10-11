"""Pruebas e2e de la promocion HTTP (PATCH /api/v1/users/{id}/role)."""

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
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.services.jwt_token_service import JwtTokenService

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/blog_test",
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
    username: str, email: str, password: str = "password12", role: str = "USER"
) -> int:
    """Crea un usuario directo en la base de pruebas y devuelve su id."""
    session = TestingSession()
    try:
        saved = PostgresUserRepository(session).save(
            User(
                username=username,
                email=email,
                password_hash=BcryptPasswordHasher().hash(password),
                role=role,  # type: ignore[arg-type]
            )
        )
        assert saved.id is not None
        return saved.id
    finally:
        session.close()


def _token(user_id: int, username: str, role: str) -> str:
    """Emite un token firmado con el secreto de pruebas."""
    return JwtTokenService(secret_key=TEST_SECRET).issue_token(
        user_id=str(user_id), username=username, role=role
    )


def _role_of(user_id: int) -> str | None:
    """Lee el rol actual del usuario directo de la base."""
    session = TestingSession()
    try:
        model = session.get(UserModel, user_id)
        return model.role if model is not None else None
    finally:
        session.close()


def test_admin_promotion_returns_200_and_admin():
    """Un ADMIN otorga ADMIN a un USER existente."""
    admin_id = _create_user("adminuser01", "admin@mail.com", role="ADMIN")
    target_id = _create_user("targetuser01", "target@mail.com", role="USER")

    response = client.patch(
        f"/api/v1/users/{target_id}/role",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {_token(admin_id, 'adminuser01', 'ADMIN')}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
    assert _role_of(target_id) == "ADMIN"


def test_user_token_returns_403_without_changes():
    """Un USER no puede otorgar ADMIN (el objetivo no cambia)."""
    _create_user("adminuser01", "admin@mail.com", role="ADMIN")
    user_id = _create_user("plainuser01", "plain@mail.com", role="USER")
    target_id = _create_user("targetuser01", "target@mail.com", role="USER")

    response = client.patch(
        f"/api/v1/users/{target_id}/role",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {_token(user_id, 'plainuser01', 'USER')}"},
    )

    assert response.status_code == 403
    assert _role_of(target_id) == "USER"


def test_missing_token_returns_401():
    """Sin token la promocion da 401."""
    target_id = _create_user("targetuser01", "target@mail.com", role="USER")

    response = client.patch(f"/api/v1/users/{target_id}/role", json={"role": "ADMIN"})

    assert response.status_code == 401
    assert _role_of(target_id) == "USER"


def test_unknown_target_returns_404():
    """Promocionar un usuario inexistente da 404."""
    admin_id = _create_user("adminuser01", "admin@mail.com", role="ADMIN")

    response = client.patch(
        "/api/v1/users/999999/role",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {_token(admin_id, 'adminuser01', 'ADMIN')}"},
    )

    assert response.status_code == 404


def test_invalid_role_returns_400():
    """Un rol distinto de ADMIN da 400 y no cambia nada."""
    admin_id = _create_user("adminuser01", "admin@mail.com", role="ADMIN")
    target_id = _create_user("targetuser01", "target@mail.com", role="USER")

    response = client.patch(
        f"/api/v1/users/{target_id}/role",
        json={"role": "USER"},
        headers={"Authorization": f"Bearer {_token(admin_id, 'adminuser01', 'ADMIN')}"},
    )

    assert response.status_code == 400
    assert _role_of(target_id) == "USER"


def test_no_logout_or_recovery_routes_exist():
    """No existen rutas de logout ni de recuperacion (dan 404)."""
    assert client.post("/api/v1/users/logout").status_code == 404
    assert client.post("/api/v1/users/password-reset").status_code == 404
    assert client.get("/api/v1/users/verify-email").status_code == 404
