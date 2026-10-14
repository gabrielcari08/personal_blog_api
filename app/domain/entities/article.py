"""Entidad de dominio para el articulo."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.exceptions.article_exceptions import ArticleValidationException

# Limites de negocio segun la especificacion.
TITLE_MIN_LENGTH = 8
TITLE_MAX_LENGTH = 20
TEXT_MIN_LENGTH = 10
TEXT_MAX_LENGTH = 300


def validate_title(title: str) -> None:
    """Valida la longitud del titulo sobre el valor crudo sin recortar."""
    # El titulo vacio tambien cae aqui con el mismo mensaje de rango.
    if not isinstance(title, str) or len(title) < TITLE_MIN_LENGTH or len(title) > TITLE_MAX_LENGTH:
        raise ArticleValidationException("title must be 8-20 characters.")


def validate_text(text: str) -> None:
    """Valida presencia y longitud del texto sobre el valor crudo sin recortar."""
    # Solo la cadena exactamente vacia es "requerida"; los blancos cuentan.
    if not isinstance(text, str) or text == "":
        raise ArticleValidationException("text is required.")
    if len(text) < TEXT_MIN_LENGTH or len(text) > TEXT_MAX_LENGTH:
        raise ArticleValidationException("text must be 10-300 characters.")


# Definicion del articulo como entidad de dominio.
@dataclass
class Article:
    """Representa un articulo del blog con sus invariantes de negocio."""

    title: str
    user_id: int
    text: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Valida los invariantes despues de construir la entidad."""
        self._validate_title(self.title)
        self._validate_user_id(self.user_id)
        self._validate_text(self.text)

    @staticmethod
    def _validate_title(title: str) -> None:
        """Delega la regla de titulo al ayudante reutilizable (sin recorte)."""
        validate_title(title)

    @staticmethod
    def _validate_text(text: str) -> None:
        """Delega la regla de texto al ayudante reutilizable (sin recorte)."""
        validate_text(text)

    @staticmethod
    def _validate_user_id(user_id: int) -> None:
        """Valida que el autor este presente (lo asigna el sistema)."""
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise ArticleValidationException("Author is required.")
