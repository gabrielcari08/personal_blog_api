"""Pruebas unitarias del servicio de tokens JWT."""

import pytest
from jose import jwt

from app.domain.services.token_service import TokenService
from app.infrastructure.services.jwt_token_service import JwtTokenService

# Secreto solo para las pruebas (nunca se escribe en el codigo fuente).
TEST_SECRET = "test-secret-key"


def test_implements_domain_interface():
    """El servicio respeta el contrato del dominio."""
    assert isinstance(JwtTokenService(secret_key=TEST_SECRET), TokenService)


def test_token_decodes_with_expected_claims():
    """El token decodifica con sub, username y rol esperados."""
    service = JwtTokenService(secret_key=TEST_SECRET)

    token = service.issue_token(user_id="1", username="validuser01", role="USER")
    claims = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    assert claims["sub"] == "1"
    assert claims["username"] == "validuser01"
    assert claims["role"] == "USER"


def test_admin_role_is_preserved():
    """El rol ADMIN viaja en el token."""
    service = JwtTokenService(secret_key=TEST_SECRET)

    token = service.issue_token(user_id="2", username="adminuser01", role="ADMIN")
    claims = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    assert claims["role"] == "ADMIN"


def test_missing_secret_raises_configuration_error(monkeypatch):
    """Sin secreto (ni inyectado ni en entorno) falla rapido."""
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValueError):
        JwtTokenService(secret_key=None)
