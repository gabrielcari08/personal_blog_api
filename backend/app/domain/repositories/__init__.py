"""Repositorios del dominio."""

from app.domain.repositories.article_repository import ArticleRepository
from app.domain.repositories.user_repository import UserRepository

__all__ = ["UserRepository", "ArticleRepository"]
