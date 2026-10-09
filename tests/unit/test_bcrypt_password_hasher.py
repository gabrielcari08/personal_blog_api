"""Pruebas unitarias del cifrador Bcrypt."""

from app.domain.services.password_hasher_service import PasswordHasher
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher


def test_implements_domain_interface():
    """El cifrador respeta el contrato del dominio."""
    assert isinstance(BcryptPasswordHasher(), PasswordHasher)


def test_hash_differs_from_plain_text():
    """El hash nunca expone la clave en texto plano."""
    hasher = BcryptPasswordHasher()

    hashed = hasher.hash("password12")

    assert hashed != "password12"
    assert "password12" not in hashed


def test_verify_accepts_correct_password():
    """La clave correcta se verifica contra su hash."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("password12")

    assert hasher.verify("password12", hashed) is True


def test_verify_rejects_wrong_password():
    """Una clave distinta no se verifica."""
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("password12")

    assert hasher.verify("wrongpass12", hashed) is False


def test_verify_rejects_malformed_hash():
    """Un hash con formato invalido se rechaza sin excepcion."""
    hasher = BcryptPasswordHasher()

    assert hasher.verify("password12", "not-a-hash") is False
