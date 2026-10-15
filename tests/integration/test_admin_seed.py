"""Pruebas de integracion del seed de administrador."""

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.user import User
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.seeds.admin_seed import ensure_admin_exists
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/blog_test",
)

engine = create_engine(TEST_URL)
TestingSession = sessionmaker(bind=engine)

# Credenciales solo para las pruebas (no son las reales del entorno).
SEED_USERNAME = "seedadmin01"
SEED_EMAIL = "seedadmin@mail.com"
SEED_PASSWORD = "seedpass12"


@pytest.fixture(scope="module", autouse=True)
def _tables() -> Generator[None, None, None]:
    """Crea las tablas una vez para todo el modulo."""
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """Entrega una sesion limpia con entorno del seed configurado."""
    monkeypatch.setenv("ADMIN_USERNAME", SEED_USERNAME)
    monkeypatch.setenv("ADMIN_EMAIL", SEED_EMAIL)
    monkeypatch.setenv("ADMIN_PASSWORD", SEED_PASSWORD)
    current: Session = TestingSession()
    yield current
    current.execute(text("TRUNCATE users RESTART IDENTITY"))
    current.commit()
    current.close()


def _count_admins(session: Session) -> int:
    """Cuenta las filas de la tabla users."""
    return session.query(UserModel).count()


def test_empty_db_creates_single_admin(session: Session):
    """Sin usuarios, el seed crea exactamente un ADMIN con la clave cifrada."""
    result = ensure_admin_exists(session, BcryptPasswordHasher())

    assert result == "created"
    assert _count_admins(session) == 1
    admin = session.query(UserModel).first()
    assert admin is not None
    assert admin.username == SEED_USERNAME
    assert admin.email == SEED_EMAIL
    assert admin.role == "ADMIN"
    assert admin.password_hash != SEED_PASSWORD
    assert BcryptPasswordHasher().verify(SEED_PASSWORD, admin.password_hash)


def test_rerun_changes_nothing(session: Session):
    """Reejecutar el seed no duplica ni degrada al administrador."""
    first = ensure_admin_exists(session, BcryptPasswordHasher())
    before = session.query(UserModel).first()
    assert before is not None

    result = ensure_admin_exists(session, BcryptPasswordHasher())

    assert first == "created"
    assert result == "already_exists"
    assert _count_admins(session) == 1
    after = session.query(UserModel).first()
    assert after is not None
    assert after.id == before.id
    assert after.role == "ADMIN"


def test_existing_email_different_case_prevents_duplicates(session: Session):
    """Un correo existente con otras mayusculas evita duplicados."""
    session.add(
        UserModel(
            username="otheradmin01",
            email="Admin@mail.com",
            email_normalized="admin@mail.com",
            password_hash="hashed",
            role="ADMIN",
        )
    )
    session.commit()

    result = ensure_admin_exists(session, BcryptPasswordHasher())

    assert result == "already_exists"
    assert _count_admins(session) == 1


def test_missing_env_fails_without_creating_user(
    session: Session, monkeypatch: pytest.MonkeyPatch
):
    """Sin configuracion en el entorno falla rapido y no crea nada."""
    monkeypatch.delenv("ADMIN_USERNAME")
    monkeypatch.delenv("ADMIN_EMAIL")
    monkeypatch.delenv("ADMIN_PASSWORD")

    with pytest.raises(ValueError):
        ensure_admin_exists(session, BcryptPasswordHasher())

    assert _count_admins(session) == 0


def test_existing_admin_with_other_email_means_no_change(session: Session):
    """Si ya hay un ADMIN (aunque sea otro correo), no se crea ninguno."""
    session.add(
        UserModel(
            username="realadmin01",
            email="real@mail.com",
            email_normalized="real@mail.com",
            password_hash="hashed",
            role="ADMIN",
        )
    )
    session.commit()

    result = ensure_admin_exists(session, BcryptPasswordHasher())

    assert result == "already_exists"
    assert _count_admins(session) == 1
    assert session.query(UserModel).first().username == "realadmin01"


def test_user_entity_accepts_seeded_admin(session: Session):
    """El ADMIN creado cumple las invariantes de la entidad de dominio."""
    ensure_admin_exists(session, BcryptPasswordHasher())

    model = session.query(UserModel).first()
    assert model is not None
    user = User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        role=model.role,
    )

    assert user.role == "ADMIN"
