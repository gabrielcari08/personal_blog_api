"""Pruebas unitarias de ListArticles y GetArticle (lectura publica)."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pytest

from app.application.use_cases.article.get_article import GetArticle
from app.application.use_cases.article.list_articles import ListArticles
from app.domain.entities.article import Article
from app.domain.exceptions.article_exceptions import ArticleNotFoundException
from app.domain.repositories.article_repository import ArticleRepository

# Tiempos fijos para ordenar los articulos semilla.
NOW = datetime.now(timezone.utc)


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
        """Lista ordenada por tiempo y luego por id, ambos descendentes."""
        return sorted(
            self._by_id.values(),
            key=lambda item: (item.created_at, item.id or 0),
            reverse=True,
        )

    def save(self, article: Article) -> Article:
        """Guarda asignando id serial y conservando el tiempo indicado."""
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


def _seed(repository: InMemoryArticleRepository) -> List[Article]:
    """Guarda tres articulos en orden de insercion mezclado respecto al tiempo."""
    middle = repository.save(
        Article(
            title="Middle Art",
            user_id=1,
            text="Middle text here.",
            created_at=NOW,
        )
    )
    oldest = repository.save(
        Article(
            title="Oldest Art",
            user_id=1,
            text="Oldest text here.",
            created_at=NOW - timedelta(days=2),
        )
    )
    newest = repository.save(
        Article(
            title="Newest Art",
            user_id=2,
            text="Newest text here.",
            created_at=NOW + timedelta(days=2),
        )
    )
    return [middle, oldest, newest]


def test_list_returns_most_recent_first_without_auth():
    """El listado publico viene de mas reciente a mas antiguo sin paginacion."""
    repository = InMemoryArticleRepository()
    _, _, newest = _seed(repository)

    listed = ListArticles(repository).execute()

    assert [item.id for item in listed] == [newest.id, 1, 2]
    assert listed[0].title == "Newest Art"
    # La salida expone el autor para la logica de ocultar acciones.
    assert listed[0].user_id == 2


def test_list_tiebreak_by_id():
    """Con igual tiempo, el id mayor va primero."""
    repository = InMemoryArticleRepository()
    first = repository.save(
        Article(title="First Tit", user_id=1, text="First text here.", created_at=NOW)
    )
    second = repository.save(
        Article(title="Second Ti", user_id=1, text="Second text here.", created_at=NOW)
    )

    listed = ListArticles(repository).execute()

    assert [item.id for item in listed] == [second.id, first.id]


def test_list_empty_without_articles():
    """Sin articulos el listado es vacio."""
    assert ListArticles(InMemoryArticleRepository()).execute() == []


def test_get_returns_article_without_auth():
    """La lectura individual es publica e incluye autor y tiempo."""
    repository = InMemoryArticleRepository()
    _, _, newest = _seed(repository)
    assert newest.id is not None

    output = GetArticle(repository).execute(newest.id)

    assert output.title == "Newest Art"
    assert output.user_id == 2
    assert output.created_at == NOW + timedelta(days=2)


def test_get_missing_raises_not_found():
    """Un id inexistente da no-encontrado."""
    with pytest.raises(ArticleNotFoundException):
        GetArticle(InMemoryArticleRepository()).execute(999999)
