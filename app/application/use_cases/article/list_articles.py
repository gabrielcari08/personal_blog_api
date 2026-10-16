"""Caso de uso para listar articulos (lectura publica, sin autenticacion)."""

from app.application.dtos.article_dtos import ArticleOutput
from app.domain.repositories.article_repository import ArticleRepository


class ListArticles:
    """Orquesta el listado publico ordenado de mas reciente a mas antiguo."""

    def __init__(self, repository: ArticleRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(self) -> list[ArticleOutput]:
        """Devuelve todos los articulos sin filtros ni paginacion."""
        # Sin contexto de autenticacion: la lectura es publica.
        # El orden lo garantiza el repositorio (created_at DESC, id DESC).
        return [
            ArticleOutput(
                id=article.id,  # type: ignore[arg-type]
                title=article.title,
                text=article.text,
                user_id=article.user_id,
                created_at=article.created_at,  # type: ignore[arg-type]
            )
            for article in self._repository.list_all_desc()
        ]
