"""Pruebas unitarias del caso de uso DeleteArticle (autor o admin)."""

from typing import Dict, List, Optional

import pytest

from app.application.use_cases.article.delete_article import DeleteArticle
from app.domain.entities.article import Article
from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import (
    ArticleForbiddenException,
    ArticleNotFoundException,
)
from app.domain.repositories.article_repository import ArticleRepository

# Identidades para las pruebas de autorizacion.
OWNER_ID = 7
OTHER_ID = 9
ADMIN_ID = 42


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
        """Guarda asignando id serial."""
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
        if article_id not in self._by_id:
            raise ArticleNotFoundException("Article not found.")
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
        Article(title="Original T", user_id=OWNER_ID, text="Original text here.")
    )
    return repository, DeleteArticle(repository), saved


def test_owner_delete_removes_article():
    """El autor elimina y el articulo desaparece del detalle y del listado."""
    repository, use_case, saved = _seeded()
    assert saved.id is not None

    use_case.execute(_user(OWNER_ID), saved.id)

    assert repository.get_by_id(saved.id) is None
    assert repository.list_all_desc() == []


def test_admin_delete_of_other_article_removes_it():
    """Un ADMIN elimina el articulo ajeno."""
    repository, use_case, saved = _seeded()
    assert saved.id is not None

    use_case.execute(_user(ADMIN_ID, role="ADMIN"), saved.id)

    assert repository.get_by_id(saved.id) is None


def test_non_owner_delete_raises_forbidden_without_removing():
    """El intento directo de un USER ajeno se rechaza sin borrar nada."""
    repository, use_case, saved = _seeded()
    assert saved.id is not None

    with pytest.raises(ArticleForbiddenException):
        use_case.execute(_user(OTHER_ID), saved.id)

    assert repository.get_by_id(saved.id) is not None


def test_delete_missing_raises_not_found():
    """Eliminar un id inexistente da no-encontrado."""
    _, use_case, _ = _seeded()

    with pytest.raises(ArticleNotFoundException):
        use_case.execute(_user(OWNER_ID), 999999)
