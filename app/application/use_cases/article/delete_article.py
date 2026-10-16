"""Caso de uso para eliminar articulos (solo autor o administrador)."""

from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import (
    ArticleForbiddenException,
    ArticleNotFoundException,
)
from app.domain.repositories.article_repository import ArticleRepository


class DeleteArticle:
    """Orquesta la eliminacion definitiva con la misma autorizacion que editar."""

    def __init__(self, repository: ArticleRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(self, caller: User, article_id: int) -> None:
        """Elimina la fila sin confirmacion ni recuperacion."""
        target = self._repository.get_by_id(article_id)
        if target is None:
            raise ArticleNotFoundException("Article not found.")

        # Autorizacion identica a la edicion: autor o administrador.
        if caller.id != target.user_id and caller.role != "ADMIN":
            raise ArticleForbiddenException("Only the author or an admin can delete.")

        self._repository.delete(article_id)
