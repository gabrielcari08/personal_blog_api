"""Rutas HTTP de usuarios (registro, login y promocion)."""

from fastapi import APIRouter, Depends, status

from app.application.dtos.user_dtos import (
    LoginInput,
    LoginOutput,
    PromoteInput,
    RegisterInput,
)
from app.application.use_cases.user.login_user import LoginUser
from app.application.use_cases.user.promote_user import PromoteUser
from app.application.use_cases.user.register_user import RegisterUser
from app.domain.entities.user import User
from app.entrypoints.api.v1.dependencies import (
    get_login_user,
    get_promote_user,
    get_register_user,
    require_admin,
)

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


@router.post("/login", response_model=LoginOutput)
def login(
    data: LoginInput, # Objeto DTO de tipo LoginInput
    use_case: LoginUser = Depends(get_login_user),
) -> LoginOutput:
    """Autentica por email o username y devuelve el token (401 generico si falla)."""
    
    # Retorna el DTO con el token.
    return use_case.execute(data) 


@router.patch("/{user_id}/role")
def promote(
    user_id: int,
    data: PromoteInput,
    admin: User = Depends(require_admin),
    use_case: PromoteUser = Depends(get_promote_user),
) -> dict:
    """Otorga ADMIN a un usuario existente (solo ADMIN)."""
    output = use_case.execute(
        requester=admin, target_user_id=user_id, new_role=data.role
    )
    return {
        "id": output.id,
        "username": output.username,
        "email": output.email,
        "role": output.role,
    }
