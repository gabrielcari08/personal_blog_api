"""Pruebas unitarias de los DTOs de usuario."""

import pytest
from pydantic import ValidationError

from app.application.dtos.user_dtos import (
    LoginInput,
    PromoteInput,
    RegisterInput,
)


def test_register_email_trimmed_and_accepted():
    """El correo con espacios alrededor se recorta y se acepta."""
    data = RegisterInput(
        username="validuser01",
        email="  user@mail.com  ",
        password="password12",
    )

    assert data.email == "user@mail.com"


def test_register_invalid_email_rejected():
    """El correo con formato invalido se rechaza."""
    with pytest.raises(ValidationError):
        RegisterInput(
            username="validuser01",
            email="not-an-email",
            password="password12",
        )


def test_register_whitespace_only_email_rejected():
    """El correo con solo blancos se rechaza como vacio."""
    with pytest.raises(ValidationError):
        RegisterInput(
            username="validuser01",
            email="   ",
            password="password12",
        )


def test_register_missing_fields_rejected():
    """Los campos ausentes o vacios se rechazan."""
    with pytest.raises(ValidationError):
        RegisterInput(username="validuser01", email="user@mail.com")

    with pytest.raises(ValidationError):
        RegisterInput(email="user@mail.com", password="password12")

    with pytest.raises(ValidationError):
        RegisterInput(username="", email="user@mail.com", password="password12")

    with pytest.raises(ValidationError):
        RegisterInput(username="validuser01", email="user@mail.com", password="")


def test_register_has_no_role_field():
    """El registro no acepta rol del cliente (se ignora el extra)."""
    data = RegisterInput(
        username="validuser01",
        email="user@mail.com",
        password="password12",
        role="ADMIN",  # type: ignore[call-arg]
    )

    assert "role" not in data.model_dump()


def test_login_identifier_not_trimmed():
    """El identificador de login se conserva tal cual (sin recorte)."""
    data = LoginInput(identifier=" user01AB ", password="password12")

    assert data.identifier == " user01AB "


def test_login_missing_fields_rejected():
    """El login sin identificador o clave se rechaza."""
    with pytest.raises(ValidationError):
        LoginInput(identifier="", password="password12")

    with pytest.raises(ValidationError):
        LoginInput(identifier="validuser01", password="")


def test_promote_accepts_admin():
    """La promocion acepta el rol ADMIN."""
    data = PromoteInput(role="ADMIN")

    assert data.role == "ADMIN"


def test_promote_rejects_non_admin_roles():
    """La promocion rechaza cualquier rol distinto de ADMIN."""
    with pytest.raises(ValidationError):
        PromoteInput(role="USER")

    with pytest.raises(ValidationError):
        PromoteInput(role="SUPER")
