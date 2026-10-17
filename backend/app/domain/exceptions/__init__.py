"""Excepciones del dominio (usuarios y articulos)."""

from app.domain.exceptions.article_exceptions import (
    ArticleForbiddenException,
    ArticleNotFoundException,
    ArticleValidationException,
)
from app.domain.exceptions.user_exceptions import (
    DuplicateEmailException,
    DuplicateUsernameException,
    ForbiddenException,
    InvalidCredentialsException,
    UserNotFoundException,
    UserValidationException,
)

__all__ = [
    "UserValidationException",
    "DuplicateUsernameException",
    "DuplicateEmailException",
    "InvalidCredentialsException",
    "ForbiddenException",
    "UserNotFoundException",
    "ArticleValidationException",
    "ArticleNotFoundException",
    "ArticleForbiddenException",
]
