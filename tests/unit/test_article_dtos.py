"""Pruebas unitarias de los DTOs de articulos."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.application.dtos.article_dtos import (
    ArticleCreateInput,
    ArticleOutput,
    ArticleUpdateInput,
)
from app.domain.exceptions.article_exceptions import ArticleValidationException

# Valores base validos para construir los DTOs en cada prueba.
VALID_TITLE = "Valid Titl"
VALID_TEXT = "This is a valid text."


def test_create_valid_inputs_preserved_without_trimming():
    """Los blancos extremos se conservan tal cual (sin recorte)."""
    data = ArticleCreateInput(title="  abcdef  ", text="  abcdefgh  ")

    assert data.title == "  abcdef  "
    assert data.text == "  abcdefgh  "


def test_update_valid_inputs_preserved():
    """La edicion acepta la misma forma valida que la creacion."""
    data = ArticleUpdateInput(title=VALID_TITLE, text=VALID_TEXT)

    assert data.title == VALID_TITLE
    assert data.text == VALID_TEXT


def test_create_short_title_rejected_with_exact_message():
    """Titulo de 7 caracteres se rechaza con el mensaje exacto."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        ArticleCreateInput(title="t" * 7, text=VALID_TEXT)


def test_create_long_title_rejected_with_exact_message():
    """Titulo de 21 caracteres se rechaza con el mensaje exacto."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        ArticleCreateInput(title="t" * 21, text=VALID_TEXT)


def test_create_empty_title_rejected_with_range_message():
    """Titulo vacio se rechaza con el mensaje de rango (no generico)."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        ArticleCreateInput(title="", text=VALID_TEXT)


def test_create_empty_text_rejected_with_required_message():
    """Texto vacio se rechaza con el mensaje de requerido."""
    with pytest.raises(ArticleValidationException, match="text is required"):
        ArticleCreateInput(title=VALID_TITLE, text="")


def test_create_short_text_rejected_with_range_message():
    """Texto de 9 caracteres se rechaza con el mensaje de rango."""
    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        ArticleCreateInput(title=VALID_TITLE, text="x" * 9)


def test_create_long_text_rejected_with_range_message():
    """Texto de 301 caracteres se rechaza con el mensaje de rango."""
    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        ArticleCreateInput(title=VALID_TITLE, text="x" * 301)


def test_update_rejects_invalid_values_with_exact_messages():
    """La edicion aplica las mismas reglas exactas que la creacion."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        ArticleUpdateInput(title="short", text=VALID_TEXT)

    with pytest.raises(ArticleValidationException, match="text is required"):
        ArticleUpdateInput(title=VALID_TITLE, text="")


def test_create_missing_fields_rejected():
    """Los campos ausentes se rechazan como error de forma."""
    with pytest.raises(ValidationError):
        ArticleCreateInput(text=VALID_TEXT)

    with pytest.raises(ValidationError):
        ArticleCreateInput(title=VALID_TITLE)


def test_create_ignores_author_and_time_from_client():
    """El cliente no puede imponer autor ni tiempo (se ignoran los extras)."""
    data = ArticleCreateInput(
        title=VALID_TITLE,
        text=VALID_TEXT,
        user_id=99,  # type: ignore[call-arg]
        created_at=datetime.now(timezone.utc).isoformat(),  # type: ignore[call-arg]
    )

    assert "user_id" not in data.model_dump()
    assert "created_at" not in data.model_dump()


def test_emoji_and_newlines_preserved_and_counted():
    """Emoji y saltos se conservan y cuentan como un caracter."""
    data = ArticleCreateInput(title="abcdefg\U0001F600", text="abcdefgh\n\n")

    assert data.title == "abcdefg\U0001F600"
    assert data.text == "abcdefgh\n\n"


def test_output_includes_author_for_hide_logic():
    """La salida expone el autor para decidir la visibilidad de acciones."""
    output = ArticleOutput(
        id=1,
        title=VALID_TITLE,
        text=VALID_TEXT,
        user_id=7,
        created_at=datetime.now(timezone.utc),
    )

    assert output.user_id == 7
    assert output.title == VALID_TITLE
