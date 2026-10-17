"""Excepciones del dominio de usuario.

Define los errores de negocio para registro, login y promocion de roles.
No incluye detalles tecnicos ni mensajes especificos de infraestructura.
"""


class UserValidationException(Exception):
    """Error de validacion de datos de usuario."""

    pass


class DuplicateUsernameException(Exception):
    """El nombre de usuario ya esta registrado (comparacion exacta)."""

    pass


class DuplicateEmailException(Exception):
    """El correo ya esta registrado (comparacion sin mayusculas)."""

    pass


class InvalidCredentialsException(Exception):
    """Credenciales invalidas sin indicar la causa exacta."""

    pass


class ForbiddenException(Exception):
    """Accion no permitida por falta de rol administrador."""

    pass


class UserNotFoundException(Exception):
    """El usuario objetivo no existe."""

    pass
