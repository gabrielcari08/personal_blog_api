"""Objetos de transferencia de la aplicacion para articulos."""

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.domain.entities.article import validate_text, validate_title

# DTOs de entrada (sin recorte: los blancos cuentan en la longitud).


class ArticleCreateInput(BaseModel):
    """Datos de entrada para crear un articulo (autor y tiempo los asigna el sistema)."""

    # Sin min_length: el vacio lo rechaza el dominio con el mensaje exacto.
    title: str
    text: str

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        """Aplica la regla de titulo del dominio (8-20, sin recortar)."""
        validate_title(value)
        return value

    @field_validator("text")
    @classmethod
    def check_text(cls, value: str) -> str:
        """Aplica la regla de texto del dominio (requerido, 10-300, sin recortar)."""
        validate_text(value)
        return value


class ArticleUpdateInput(BaseModel):
    """Datos de entrada para editar un articulo (reemplazo total, misma forma que crear)."""

    # Sin min_length: el vacio lo rechaza el dominio con el mensaje exacto.
    title: str
    text: str

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        """Aplica la regla de titulo del dominio (8-20, sin recortar)."""
        validate_title(value)
        return value

    @field_validator("text")
    @classmethod
    def check_text(cls, value: str) -> str:
        """Aplica la regla de texto del dominio (requerido, 10-300, sin recortar)."""
        validate_text(value)
        return value


# DTO de salida.


class ArticleOutput(BaseModel):
    """Datos de salida de un articulo (incluye autor para ocultar acciones)."""

    id: int
    title: str
    text: str
    user_id: int
    created_at: datetime
