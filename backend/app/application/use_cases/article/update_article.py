"""Caso de uso para editar articulos (solo autor o administrador)."""

from dataclasses import replace

from app.application.dtos.article_dtos import ArticleOutput, ArticleUpdateInput
from app.domain.entities.user import User
from app.domain.exceptions.article_exceptions import (
    ArticleForbiddenException,
    ArticleNotFoundException,
)
from app.domain.repositories.article_repository import ArticleRepository


class UpdateArticle:
    """Orquesta la edicion: autoriza, reconstruye con historia y guarda."""

    def __init__(self, repository: ArticleRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(
        self, caller: User, article_id: int, data: ArticleUpdateInput
    ) -> ArticleOutput:
        """Reemplaza titulo y texto conservando autor y tiempo originales."""
        target = self._repository.get_by_id(article_id)
        if target is None:
            raise ArticleNotFoundException("Article not found.")

        # Autorizacion: el autor o un administrador (el rol viene del token).
        # Esto frena tambien el intento directo que evade los botones ocultos.
        if caller.id != target.user_id and caller.role != "ADMIN":
            raise ArticleForbiddenException("Only the author or an admin can edit.")

        # Reconstruccion con historia: replace conserva id, autor y tiempo.
        # La entidad revalida los valores nuevos con los mensajes exactos.
        updated = replace(target, title=data.title, text=data.text)
        stored = self._repository.update(updated)

        return ArticleOutput(
            id=stored.id,  # type: ignore[arg-type]
            title=stored.title,
            text=stored.text,
            user_id=stored.user_id,
            created_at=stored.created_at,  # type: ignore[arg-type]
        )
