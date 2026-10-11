"""Rutas HTTP de usuarios (registro en esta entrega)."""

from fastapi import APIRouter, Depends, status

from app.application.dtos.user_dtos import RegisterInput
from app.application.use_cases.user.register_user import RegisterUser
from app.entrypoints.api.v1.dependencies import get_register_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterInput,
    use_case: RegisterUser = Depends(get_register_user),
) -> dict:
    """Registra un usuario (siempre USER) e indica ir al login."""
    output = use_case.execute(data)
    return {
        "message": "Registration successful. Please log in.",
        "id": output.id,
        "username": output.username,
        "email": output.email,
        "role": output.role,
    }
