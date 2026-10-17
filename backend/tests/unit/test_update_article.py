"""Pruebas unitarias del caso de uso UpdateArticle (autor o admin)."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

import pytest

from app.application.dtos.article_dtos import ArticleUpdateInput
from app.application.use_cases.article.update_article import UpdateArticle
from app.domain.entities.article import Article
from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import (
    ArticleForbiddenException,
    ArticleNotFoundException,
    ArticleValidationException,
)
from app.domain.repositories.article_repository import ArticleRepository

# Identidades para las pruebas de autorizacion.
OWNER_ID = 7
OTHER_ID = 9
ADMIN_ID = 42
CREATED = datetime(2026, 1, 1, tzinfo=timezone.utc)


class InMemoryArticleRepository(ArticleRepository):
    """Repositorio falso en memoria para las pruebas."""

    def __init__(self) -> None:
        """Inicializa el indice por id y el serial."""
        self._by_id: Dict[int, Article] = {}
        self._next_id = 1

    def get_by_id(self, article_id: int) -> Optional[Article]:
        """Busca por id."""
        return self._by_id.get(article_id)

    def list_all_desc(self) -> List[Article]:
        """Lista de mas reciente a mas antiguo (por id como desempate)."""
        return sorted(self._by_id.values(), key=lambda item: item.id or 0, reverse=True)

    def save(self, article: Article) -> Article:
        """Guarda asignando id serial y conservando autor y tiempo."""
        from dataclasses import replace

        stored = replace(article, id=self._next_id)
        self._next_id += 1
        assert stored.id is not None
        self._by_id[stored.id] = stored
        return stored

    def update(self, article: Article) -> Article:
        """Actualiza el articulo existente."""
        assert article.id is not None
        self._by_id[article.id] = article
        return article

    def delete(self, article_id: int) -> None:
        """Elimina la fila del articulo."""
        del self._by_id[article_id]


def _user(user_id: int, role: str = "USER") -> User:
    """Construye el solicitante autenticado."""
    return User(
        id=user_id,
        username=f"user{user_id:05d}",
        email=f"user{user_id}@mail.com",
        password_hash="hashed",
        role=role,
    )


def _seeded() -> tuple:
    """Entrega repositorio con un articulo del autor y el caso de uso."""
    repository = InMemoryArticleRepository()
    saved = repository.save(
        Article(
            title="Original T",
            user_id=OWNER_ID,
            text="Original text here.",
            created_at=CREATED,
        )
    )
    return repository, UpdateArticle(repository), saved


def _valid_input() -> ArticleUpdateInput:
    """Entrada valida para la edicion."""
    return ArticleUpdateInput(title="Edited Tit", text="This text was edited.")


def test_owner_update_succeeds_preserving_history():
    """El autor edita y conserva autor y tiempo originales."""
    _, use_case, saved = _seeded()
    assert saved.id is not None

    output = use_case.execute(_user(OWNER_ID), saved.id, _valid_input())

    assert output.title == "Edited Tit"
    assert output.text == "This text was edited."
    assert output.user_id == OWNER_ID
    assert output.created_at == CREATED


def test_admin_update_of_other_article_succeeds():
    """Un ADMIN edita el articulo ajeno sin cambiar su historia."""
    _, use_case, saved = _seeded()
    assert saved.id is not None

    output = use_case.execute(_user(ADMIN_ID, role="ADMIN"), saved.id, _valid_input())

    assert output.title == "Edited Tit"
    assert output.user_id == OWNER_ID
    assert output.created_at == CREATED


def test_non_owner_update_raises_forbidden_without_changes():
    """El intento directo de un USER ajeno se rechaza sin cambiar nada."""
    repository, use_case, saved = _seeded()
    assert saved.id is not None

    with pytest.raises(ArticleForbiddenException):
        use_case.execute(_user(OTHER_ID), saved.id, _valid_input())

    unchanged = repository.get_by_id(saved.id)
    assert unchanged is not None
    assert unchanged.title == "Original T"
    assert unchanged.text == "Original text here."


def test_update_missing_raises_not_found():
    """Editar un id inexistente da no-encontrado."""
    _, use_case, _ = _seeded()

    with pytest.raises(ArticleNotFoundException):
        use_case.execute(_user(OWNER_ID), 999999, _valid_input())


def test_update_with_invalid_values_keeps_originals():
    """Valores nuevos invalidos se rechazan con mensajes exactos sin cambiar nada."""
    repository, use_case, saved = _seeded()
    assert saved.id is not None

    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        use_case.execute(
            _user(OWNER_ID),
            saved.id,
            ArticleUpdateInput.model_construct(title="short", text="This text was edited."),
        )

    with pytest.raises(ArticleValidationException, match="text is required"):
        use_case.execute(
            _user(OWNER_ID),
            saved.id,
            ArticleUpdateInput.model_construct(title="Edited Tit", text=""),
        )

    unchanged = repository.get_by_id(saved.id)
    assert unchanged is not None
    assert unchanged.title == "Original T"
