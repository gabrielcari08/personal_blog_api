"""Pruebas unitarias del caso de uso CreateArticle."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

import pytest
from pydantic import ValidationError

from app.application.dtos.article_dtos import ArticleCreateInput
from app.application.use_cases.article.create_article import CreateArticle
from app.domain.entities.article import Article
from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import ArticleValidationException
from app.domain.repositories.article_repository import ArticleRepository

# Valores base validos para construir autores y articulos.
CALLER_ID = 7
VALID_TITLE = "Valid Titl"
VALID_TEXT = "This is a valid text."


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
        """Guarda asignando id serial y tiempo del servidor simulado."""
        from dataclasses import replace

        stored = replace(
            article, id=self._next_id, created_at=datetime.now(timezone.utc)
        )
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


def _caller(role: str = "USER", user_id: int = CALLER_ID) -> User:
    """Construye el usuario autenticado que ejecuta el caso de uso."""
    return User(
        id=user_id,
        username="authoruser01",
        email="author@mail.com",
        password_hash="hashed",
        role=role,
    )


def _input(title: str = VALID_TITLE, text: str = VALID_TEXT) -> ArticleCreateInput:
    """Construye la entrada valida del caso de uso."""
    return ArticleCreateInput(title=title, text=text)


def test_success_assigns_caller_as_owner():
    """Crear asigna el solicitante como autor con tiempo del servidor."""
    use_case = CreateArticle(InMemoryArticleRepository())

    output = use_case.execute(_caller(), _input())

    assert output.id == 1
    assert output.title == VALID_TITLE
    assert output.text == VALID_TEXT
    assert output.user_id == CALLER_ID
    assert output.created_at is not None
    assert output.created_at.tzinfo is not None


def test_admin_creator_owned_like_any_author():
    """Un ADMIN que crea queda como autor igual que cualquier usuario."""
    use_case = CreateArticle(InMemoryArticleRepository())

    output = use_case.execute(_caller(role="ADMIN", user_id=42), _input())

    assert output.user_id == 42


def test_values_preserved_without_trimming():
    """Los blancos extremos se guardan tal cual (sin recorte)."""
    repository = InMemoryArticleRepository()
    use_case = CreateArticle(repository)

    output = use_case.execute(_caller(), _input(title="  abcdef  ", text="  abcdefgh  "))

    assert output.title == "  abcdef  "
    assert output.text == "  abcdefgh  "


def test_short_title_fails_with_exact_message_and_saves_nothing():
    """Titulo corto se rechaza con el mensaje exacto sin guardar nada."""
    repository = InMemoryArticleRepository()
    use_case = CreateArticle(repository)

    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        use_case.execute(_caller(), ArticleCreateInput.model_construct(title="short", text=VALID_TEXT))

    assert repository.list_all_desc() == []


def test_long_title_fails_with_exact_message():
    """Titulo largo se rechaza con el mensaje exacto."""
    use_case = CreateArticle(InMemoryArticleRepository())

    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        use_case.execute(_caller(), ArticleCreateInput.model_construct(title="t" * 21, text=VALID_TEXT))


def test_empty_text_fails_with_required_message():
    """Texto vacio se rechaza con el mensaje de requerido."""
    use_case = CreateArticle(InMemoryArticleRepository())

    with pytest.raises(ArticleValidationException, match="text is required"):
        use_case.execute(_caller(), ArticleCreateInput.model_construct(title=VALID_TITLE, text=""))


def test_out_of_range_text_fails_with_range_message():
    """Texto de 9 o 301 caracteres se rechaza con el mensaje de rango."""
    use_case = CreateArticle(InMemoryArticleRepository())

    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        use_case.execute(_caller(), ArticleCreateInput.model_construct(title=VALID_TITLE, text="x" * 9))

    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        use_case.execute(_caller(), ArticleCreateInput.model_construct(title=VALID_TITLE, text="x" * 301))


def test_boundary_dto_rejects_missing_fields():
    """El DTO rechaza campos ausentes antes de llegar a la entidad."""
    with pytest.raises(ValidationError):
        ArticleCreateInput(text=VALID_TEXT)
