"""Modelos ORM de la base de datos."""

from app.infrastructure.db.models.article_model import ArticleModel
from app.infrastructure.db.models.user_model import UserModel

__all__ = ["UserModel", "ArticleModel"]
