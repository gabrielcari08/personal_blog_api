"""Repositorio de articulos en PostgreSQL (implementacion de infraestructura)."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.article import Article
from app.domain.exceptions.article_exceptions import (
    ArticleNotFoundException,
    ArticleValidationException,
)
from app.domain.repositories.article_repository import ArticleRepository
from app.infrastructure.db.models.article_model import ArticleModel


class PostgresArticleRepository(ArticleRepository):
    """Implementa ArticleRepository con SQLAlchemy sobre PostgreSQL."""

    def __init__(self, session: Session) -> None:
        """Guarda la sesion SQLAlchemy inyectada."""
        self._session = session

    def get_by_id(self, article_id: int) -> Optional[Article]:
        """Busca un articulo por su id."""
        model = self._session.get(ArticleModel, article_id)
        return self._to_entity(model) if model is not None else None

    def list_all_desc(self) -> list[Article]:
        """Lista todos los articulos de mas reciente a mas antiguo."""
        models = (
            self._session.query(ArticleModel)
            .order_by(ArticleModel.created_at.desc(), ArticleModel.id.desc())
            .all()
        )
        return [self._to_entity(model) for model in models]

    def save(self, article: Article) -> Article:
        """Guarda un articulo nuevo (el tiempo lo asigna la base de datos)."""
        model = ArticleModel(
            title=article.title,
            user_id=article.user_id,
            text=article.text,
        )
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise self._map_integrity_violation(error) from error
        self._session.refresh(model)
        return self._to_entity(model)

    def update(self, article: Article) -> Article:
        """Actualiza solo titulo y texto (autor y tiempo nunca se escriben)."""
        model = self._session.get(ArticleModel, article.id)
        if model is None:
            raise ArticleNotFoundException("Article not found.")
        model.title = article.title
        model.text = article.text
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise self._map_integrity_violation(error) from error
        self._session.refresh(model)
        return self._to_entity(model)

    def delete(self, article_id: int) -> None:
        """Elimina definitivamente la fila del articulo."""
        model = self._session.get(ArticleModel, article_id)
        if model is None:
            raise ArticleNotFoundException("Article not found.")
        self._session.delete(model)
        self._session.commit()

    @staticmethod
    def _to_entity(model: ArticleModel) -> Article:
        """Convierte una fila ORM en entidad de dominio."""
        return Article(
            id=model.id,
            title=model.title,
            user_id=model.user_id,
            text=model.text,
            created_at=model.created_at,
        )

    @staticmethod
    def _map_integrity_violation(error: IntegrityError) -> Exception:
        """Traduce la restriccion violada a la excepcion de dominio adecuada."""
        name = getattr(getattr(error, "orig", None), "diag", None)
        constraint = getattr(name, "constraint_name", "") or ""
        if "user_id" in constraint or "fkey" in constraint:
            return ArticleNotFoundException("Author not found.")
        return ArticleValidationException("Article violates a storage constraint.")
