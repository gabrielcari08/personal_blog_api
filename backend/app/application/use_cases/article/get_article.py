"""Caso de uso para ver un articulo (lectura publica, sin autenticacion)."""

from app.application.dtos.article_dtos import ArticleOutput
from app.domain.exceptions.article_exceptions import ArticleNotFoundException
from app.domain.repositories.article_repository import ArticleRepository


class GetArticle:
    """Orquesta la lectura de un articulo por su identificador."""

    def __init__(self, repository: ArticleRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(self, article_id: int) -> ArticleOutput:
        """Devuelve el articulo o un error de no-encontrado."""
        article = self._repository.get_by_id(article_id)
        if article is None:
            raise ArticleNotFoundException("Article not found.")

        return ArticleOutput(
            id=article.id,  # type: ignore[arg-type]
            title=article.title,
            text=article.text,
            user_id=article.user_id,
            created_at=article.created_at,  # type: ignore[arg-type]
        )
