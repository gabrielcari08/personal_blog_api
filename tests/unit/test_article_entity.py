"""Pruebas unitarias de la entidad de dominio Article."""

import pytest

from app.domain.entities.article import Article, validate_text, validate_title
from app.domain.exceptions.article_exceptions import ArticleValidationException

# Valores base validos para construir la entidad en cada prueba.
VALID_TITLE = "Valid Titl"
VALID_TEXT = "This is a valid text."
VALID_USER_ID = 1


def test_valid_article_preserves_values():
    """Un articulo valido conserva titulo, autor y texto sin tiempo asignado."""
    article = Article(title=VALID_TITLE, user_id=VALID_USER_ID, text=VALID_TEXT)

    assert article.title == VALID_TITLE
    assert article.user_id == VALID_USER_ID
    assert article.text == VALID_TEXT
    assert article.id is None
    assert article.created_at is None


def test_title_boundaries_accepted():
    """Titulos de 8 y 20 caracteres se aceptan."""
    Article(title="t" * 8, user_id=VALID_USER_ID, text=VALID_TEXT)
    Article(title="t" * 20, user_id=VALID_USER_ID, text=VALID_TEXT)


def test_short_title_rejected_with_exact_message():
    """Titulo de 7 caracteres se rechaza con el mensaje exacto."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        Article(title="t" * 7, user_id=VALID_USER_ID, text=VALID_TEXT)


def test_long_title_rejected_with_exact_message():
    """Titulo de 21 caracteres se rechaza con el mensaje exacto."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        Article(title="t" * 21, user_id=VALID_USER_ID, text=VALID_TEXT)


def test_empty_title_rejected_with_range_message():
    """Titulo vacio se rechaza con el mensaje de rango (sin mensaje aparte)."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        Article(title="", user_id=VALID_USER_ID, text=VALID_TEXT)


def test_text_boundaries_accepted():
    """Textos de 10 y 300 caracteres se aceptan."""
    Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="x" * 10)
    Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="x" * 300)


def test_empty_text_rejected_with_required_message():
    """Texto exactamente vacio se rechaza con el mensaje de requerido."""
    with pytest.raises(ArticleValidationException, match="text is required"):
        Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="")


def test_short_text_rejected_with_range_message():
    """Texto no vacio de 9 caracteres se rechaza con el mensaje de rango."""
    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="x" * 9)


def test_long_text_rejected_with_range_message():
    """Texto de 301 caracteres se rechaza con el mensaje de rango."""
    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="x" * 301)


def test_whitespace_only_text_counts_length():
    """Texto de 3 espacios no es vacio: cae en el error de rango."""
    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="   ")


def test_surrounding_spaces_are_not_trimmed():
    """Los espacios extremos cuentan y el valor se conserva intacto."""
    # 2 espacios + 6 letras + 2 espacios = 10, debe aceptarse sin recortar.
    article = Article(title="  abcdef  ", user_id=VALID_USER_ID, text="  abcdefgh  ")

    assert article.title == "  abcdef  "
    assert article.text == "  abcdefgh  "


def test_newlines_count_as_characters():
    """Los saltos de linea cuentan como un caracter cada uno."""
    # 8 letras + 2 saltos = 10, debe aceptarse como texto minimo.
    Article(title=VALID_TITLE, user_id=VALID_USER_ID, text="abcdefgh\n\n")


def test_emoji_counts_as_one_character():
    """Un emoji suma 1 a la longitud (7 letras + 1 emoji = 8)."""
    Article(title="abcdefg\U0001F600", user_id=VALID_USER_ID, text=VALID_TEXT)


def test_missing_author_rejected():
    """Autor ausente se rechaza (lo asigna el sistema, nunca el cliente)."""
    with pytest.raises(ArticleValidationException):
        Article(title=VALID_TITLE, user_id=None, text=VALID_TEXT)


def test_helpers_expose_same_messages():
    """Los ayudantes reutilizables lanzan los mismos mensajes exactos."""
    with pytest.raises(ArticleValidationException, match="title must be 8-20 characters."):
        validate_title("short")

    with pytest.raises(ArticleValidationException, match="text is required"):
        validate_text("")

    with pytest.raises(ArticleValidationException, match="text must be 10-300 characters."):
        validate_text("short")
