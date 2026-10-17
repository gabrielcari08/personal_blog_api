"""Pruebas unitarias de la entidad de dominio User."""

import pytest

from app.domain.entities.user import User, validate_plain_password
from app.domain.exceptions.user_exceptions import UserValidationException

# Valores base validos para construir la entidad en cada prueba.
VALID_USERNAME = "validuser01"
VALID_EMAIL = "user@mail.com"
VALID_HASH = "hashed-value"


def test_valid_user_defaults_to_user_role():
    """Un usuario valido sin rol indicado queda como USER."""
    user = User(username=VALID_USERNAME, email=VALID_EMAIL, password_hash=VALID_HASH)

    assert user.role == "USER"
    assert user.username == VALID_USERNAME


def test_valid_user_with_admin_role():
    """Un usuario valido puede crearse con rol ADMIN (solo seed o promocion)."""
    user = User(
        username=VALID_USERNAME,
        email=VALID_EMAIL,
        password_hash=VALID_HASH,
        role="ADMIN",
    )

    assert user.role == "ADMIN"


def test_short_username_rejected():
    """Username de 7 caracteres se rechaza."""
    with pytest.raises(UserValidationException):
        User(username="user123", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_long_username_rejected():
    """Username de 21 caracteres se rechaza."""
    with pytest.raises(UserValidationException):
        User(username="u" * 21, email=VALID_EMAIL, password_hash=VALID_HASH)


def test_username_boundaries_accepted():
    """Usernames de 8 y 20 caracteres se aceptan."""
    User(username="u" * 8, email=VALID_EMAIL, password_hash=VALID_HASH)
    User(username="u" * 20, email=VALID_EMAIL, password_hash=VALID_HASH)


def test_username_with_internal_space_rejected():
    """Username con espacio interno se rechaza sin recortar."""
    with pytest.raises(UserValidationException):
        User(username="my user01", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_username_with_leading_space_rejected():
    """Username con espacio inicial se rechaza sin recortar."""
    with pytest.raises(UserValidationException):
        User(username=" user01AB", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_username_with_trailing_space_rejected():
    """Username con espacio final se rechaza sin recortar."""
    with pytest.raises(UserValidationException):
        User(username="user01AB ", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_username_with_tab_rejected():
    """Username con tabulacion se rechaza como blanco."""
    with pytest.raises(UserValidationException):
        User(username="user\t01AB", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_empty_username_rejected():
    """Username vacio se rechaza."""
    with pytest.raises(UserValidationException):
        User(username="", email=VALID_EMAIL, password_hash=VALID_HASH)


def test_empty_email_rejected():
    """Email vacio se rechaza."""
    with pytest.raises(UserValidationException):
        User(username=VALID_USERNAME, email="", password_hash=VALID_HASH)


def test_whitespace_only_email_rejected():
    """Email con solo blancos se rechaza como vacio."""
    with pytest.raises(UserValidationException):
        User(username=VALID_USERNAME, email="   ", password_hash=VALID_HASH)


def test_empty_password_hash_rejected():
    """Hash vacio se rechaza (nunca se guarda la clave en plano)."""
    with pytest.raises(UserValidationException):
        User(username=VALID_USERNAME, email=VALID_EMAIL, password_hash="")


def test_plain_password_boundaries():
    """Clave en plano: 7 y 21 fallan, 8 y 20 pasan."""
    with pytest.raises(UserValidationException):
        validate_plain_password("a" * 7)

    validate_plain_password("a" * 8)
    validate_plain_password("a" * 20)

    with pytest.raises(UserValidationException):
        validate_plain_password("a" * 21)


def test_plain_password_with_spaces_counts_length():
    """La clave no se recorta: los espacios cuentan en la longitud."""
    # 2 espacios + 6 letras = 8, debe aceptarse.
    validate_plain_password("  abcdef")


def test_invalid_role_rejected():
    """Roles distintos de USER o ADMIN se rechazan."""
    with pytest.raises(UserValidationException):
        User(
            username=VALID_USERNAME,
            email=VALID_EMAIL,
            password_hash=VALID_HASH,
            role="SUPER",
        )


def test_username_case_preserved():
    """La entidad conserva las mayusculas del username."""
    user = User(username="User01AB", email=VALID_EMAIL, password_hash=VALID_HASH)

    assert user.username == "User01AB"
