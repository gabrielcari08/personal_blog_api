"""Objetos de transferencia de la aplicacion para usuarios."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

# DTOs de entrada

class RegisterInput(BaseModel):
    """Datos de entrada para el registro (el rol nunca viene del cliente)."""

    username: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: object) -> object:
        """Recorta los espacios del correo antes de validar el formato."""
        if isinstance(value, str):
            return value.strip()
        return value


class LoginInput(BaseModel):
    """Datos de entrada para el login (identificador sin recortar)."""

    # Uso de identiefer en lugar de username o email. 
    # Permite que el usuario envíe su username o email para iniciar sesion.
    identifier: str = Field(min_length=1)
    password: str = Field(min_length=1)


class PromoteInput(BaseModel):
    """Datos de entrada para otorgar el rol administrador."""

    role: Literal["ADMIN"]

# DTOs de salida

class UserOutput(BaseModel):
    """Datos de salida de un usuario."""

    id: str
    username: str
    email: str
    role: Literal["USER", "ADMIN"]


class LoginOutput(BaseModel):
    """Datos de salida de un login exitoso."""

    access_token: str
    token_type: str = "bearer"
