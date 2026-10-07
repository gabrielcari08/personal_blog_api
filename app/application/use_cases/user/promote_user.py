"""Caso de uso para otorgar el rol administrador (solo ADMIN)."""

from dataclasses import replace

from app.application.dtos.user_dtos import UserOutput
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    ForbiddenException,
    UserNotFoundException,
    UserValidationException,
)
from app.domain.repositories.user_repository import UserRepository


class PromoteUser:
    """Orquesta la promocion: autoriza, localiza y actualiza el rol."""

    def __init__(self, repository: UserRepository) -> None:
        """Guarda el repositorio inyectado."""
        self._repository = repository

    def execute(
        self, requester: User, target_user_id: int, new_role: str
    ) -> UserOutput:
        """Otorga ADMIN al objetivo (solo un ADMIN puede hacerlo)."""
        # Autorizacion: el rol del solicitante viene del token validado.
        if requester.role != "ADMIN":
            raise ForbiddenException("Only admins can grant the admin role.")

        # Regla de la operacion: esta via solo otorga ADMIN.
        if new_role != "ADMIN":
            raise UserValidationException("Role must be ADMIN.")

        target = self._repository.get_by_id(target_user_id)
        if target is None:
            raise UserNotFoundException("User not found.")

        # La entidad valida el rol en __post_init__ (solo USER o ADMIN).
        # updated: Almacena la nueva instancia del usuario con el rol actualizado.
        updated = replace(target, role=new_role)
        # saved: Almacena el usuario actualizado.
        saved = self._repository.update(updated)

        return UserOutput(
            id=saved.id,  # type: ignore[arg-type]
            username=saved.username,
            email=saved.email,
            role=saved.role,  # type: ignore[arg-type]
        )
