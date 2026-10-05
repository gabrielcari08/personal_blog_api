"""Excepciones del dominio de usuario."""

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
]
