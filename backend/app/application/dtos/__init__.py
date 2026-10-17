"""DTOs de la aplicacion."""

from app.application.dtos.article_dtos import (
    ArticleCreateInput,
    ArticleOutput,
    ArticleUpdateInput,
)
from app.application.dtos.user_dtos import (
    LoginInput,
    LoginOutput,
    PromoteInput,
    RegisterInput,
    UserOutput,
)

__all__ = [
    "RegisterInput",
    "LoginInput",
    "PromoteInput",
    "UserOutput",
    "LoginOutput",
    "ArticleCreateInput",
    "ArticleUpdateInput",
    "ArticleOutput",
]
