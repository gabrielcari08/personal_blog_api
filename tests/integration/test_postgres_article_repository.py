"""Pruebas de integracion del repositorio Postgres de articulos."""

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities.article import Article
from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import ArticleNotFoundException
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.article_model import ArticleModel
from app.infrastructure.repositories.postgres_article_repository import (
    PostgresArticleRepository,
)
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)

# Base de datos de pruebas (nunca la de desarrollo).
TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/blog_test",
)

engine = create_engine(TEST_URL)
TestingSession = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def _tables() -> Generator[None, None, None]:
    """Crea las tablas una vez para todo el modulo."""
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    """Entrega una sesion limpia por prueba y limpia ambas tablas al salir."""
    current: Session = TestingSession()
    yield current
    current.execute(text("TRUNCATE articles, users RESTART IDENTITY"))
    current.commit()
    current.close()


@pytest.fixture()
def repository(session: Session) -> PostgresArticleRepository:
    """Entrega el repositorio de articulos sobre la sesion de la prueba."""
    return PostgresArticleRepository(session)


@pytest.fixture()
def owner_id(session: Session) -> int:
    """Crea un usuario autor y devuelve su id (la FK lo exige)."""
    saved = PostgresUserRepository(session).save(
        User(username="authoruser01", email="author@mail.com", password_hash="hashed")
    )
    assert saved.id is not None
    return saved.id


def _article(user_id: int, **overrides: object) -> Article:
    """Construye un articulo valido con valores por defecto."""
    data: dict = {
        "title": "Valid Titl",
        "user_id": user_id,
        "text": "This is a valid text.",
    }
    data.update(overrides)
    return Article(**data)


def test_round_trip_persists_all_fields(
    repository: PostgresArticleRepository, owner_id: int
):
    """Guardar y leer devuelve los mismos datos con tiempo asignado por el servidor."""
    saved = repository.save(_article(owner_id))

    assert saved.id is not None
    assert saved.created_at is not None
    assert saved.created_at.tzinfo is not None
    found = repository.get_by_id(saved.id)
    assert found is not None
    assert found.title == "Valid Titl"
    assert found.user_id == owner_id
    assert found.text == "This is a valid text."
    assert found.created_at == saved.created_at


def test_get_missing_returns_none(repository: PostgresArticleRepository):
    """Buscar un articulo inexistente devuelve nulo (el 404 lo decide el caso de uso)."""
    assert repository.get_by_id(999999) is None


def test_save_with_unknown_author_fails(
    repository: PostgresArticleRepository,
):
    """Guardar con un autor inexistente viola la FK y da error de dominio."""
    with pytest.raises(ArticleNotFoundException):
        repository.save(_article(999999))


def test_list_returns_most_recent_first(
    repository: PostgresArticleRepository, owner_id: int
):
    """El listado viene ordenado de mas reciente a mas antiguo."""
    first = repository.save(_article(owner_id, title="First Arti"))
    second = repository.save(_article(owner_id, title="Second Art"))
    third = repository.save(_article(owner_id, title="Third Arti"))

    listed = repository.list_all_desc()

    assert [item.id for item in listed] == [third.id, second.id, first.id]


def test_list_tiebreak_by_id(
    repository: PostgresArticleRepository, owner_id: int, session: Session
):
    """Con igual tiempo de creacion, el id mayor va primero."""
    one = repository.save(_article(owner_id, title="One Artic"))
    two = repository.save(_article(owner_id, title="Two Artic"))
    same = datetime.now(timezone.utc)
    session.execute(
        text("UPDATE articles SET created_at = :when"), {"when": same}
    )
    session.commit()

    listed = repository.list_all_desc()

    assert [item.id for item in listed] == [two.id, one.id]


def test_list_empty_when_no_articles(repository: PostgresArticleRepository):
    """Sin articulos el listado es vacio (sin paginacion que validar)."""
    assert repository.list_all_desc() == []


def test_update_changes_only_title_and_text(
    repository: PostgresArticleRepository, owner_id: int
):
    """Actualizar cambia titulo y texto conservando autor y tiempo."""
    saved = repository.save(_article(owner_id))
    assert saved.id is not None

    updated = repository.update(
        replace(saved, title="Edited Tit", text="This text was edited.")
    )

    assert updated.title == "Edited Tit"
    assert updated.text == "This text was edited."
    assert updated.user_id == owner_id
    assert updated.created_at == saved.created_at
    found = repository.get_by_id(saved.id)
    assert found is not None
    assert found.title == "Edited Tit"
    assert found.user_id == owner_id


def test_update_ignores_author_and_time(
    repository: PostgresArticleRepository, owner_id: int, session: Session
):
    """Aunque la entidad traiga otro autor o tiempo, no se escriben."""
    saved = repository.save(_article(owner_id))
    assert saved.id is not None
    other = PostgresUserRepository(session).save(
        User(username="otheruser01", email="other@mail.com", password_hash="hashed")
    )

    updated = repository.update(
        replace(
            saved,
            title="Edited Tit",
            user_id=other.id,
            text="This text was edited.",
            created_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
    )

    assert updated.user_id == owner_id
    assert updated.created_at == saved.created_at


def test_update_missing_raises_not_found(repository: PostgresArticleRepository):
    """Actualizar un articulo inexistente da no-encontrado."""
    ghost = Article(id=999999, title="Ghost Tit", user_id=1, text="Ghost text here.")

    with pytest.raises(ArticleNotFoundException):
        repository.update(ghost)


def test_delete_removes_row(
    repository: PostgresArticleRepository, owner_id: int
):
    """Eliminar quita la fila: ni el detalle ni el listado la ven."""
    saved = repository.save(_article(owner_id))
    assert saved.id is not None

    repository.delete(saved.id)

    assert repository.get_by_id(saved.id) is None
    assert repository.list_all_desc() == []


def test_delete_missing_raises_not_found(repository: PostgresArticleRepository):
    """Eliminar un articulo inexistente da no-encontrado."""
    with pytest.raises(ArticleNotFoundException):
        repository.delete(999999)


def test_check_guard_rejects_out_of_range_row(
    repository: PostgresArticleRepository, owner_id: int, session: Session
):
    """El CHECK de la base frena filas fuera de rango aunque evadan el dominio."""
    with pytest.raises(IntegrityError):
        session.execute(
            ArticleModel.__table__.insert().values(
                title="short", user_id=owner_id, text="This is a valid text."
            )
        )
        session.commit()
    session.rollback()


def test_empty_list_after_mixed_operations(
    repository: PostgresArticleRepository, owner_id: int
):
    """Crear dos y borrar uno deja exactamente el restante en el listado."""
    keep = repository.save(_article(owner_id, title="Keep This"))
    drop = repository.save(_article(owner_id, title="Drop This "))
    assert drop.id is not None

    repository.delete(drop.id)
    listed = repository.list_all_desc()

    assert [item.id for item in listed] == [keep.id]
