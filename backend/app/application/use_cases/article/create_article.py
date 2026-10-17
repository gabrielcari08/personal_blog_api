"""Caso de uso para crear articulos (el autor siempre es el solicitante)."""

from app.application.dtos.article_dtos import ArticleCreateInput, ArticleOutput
from app.domain.entities.article import Article
from app.domain.entities.user import User
from app.domain.repositories.article_repository import ArticleRepository


class CreateArticle:
    """Orquesta la creacion: construye la entidad con el autor del token y guarda."""

    def __init__(self, repository: ArticleRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(self, caller: User, data: ArticleCreateInput) -> ArticleOutput:
        """Crea un articulo owned por el solicitante y visible de inmediato."""
        # El autor es siempre el usuario autenticado: el cuerpo nunca trae user_id.
        # La entidad autovalida titulo y texto con los mensajes exactos.
        # El tiempo lo asigna la persistencia (auditoria, nunca del cliente).
        article = Article(title=data.title, user_id=caller.id, text=data.text)  # type: ignore[arg-type]
        stored = self._repository.save(article)

        return ArticleOutput(
            id=stored.id,  # type: ignore[arg-type]
            title=stored.title,
            text=stored.text,
            user_id=stored.user_id,
            created_at=stored.created_at,  # type: ignore[arg-type]
        )
