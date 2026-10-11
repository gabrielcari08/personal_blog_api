"""Inyeccion de dependencias de la API v1 (sesion, casos de uso y guardias)."""

import os
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.use_cases.user.login_user import LoginUser
from app.application.use_cases.user.promote_user import PromoteUser
from app.application.use_cases.user.register_user import RegisterUser
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.password_hasher_service import PasswordHasher
from app.domain.services.token_service import TokenService
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from app.infrastructure.services.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.services.jwt_token_service import JwtTokenService

# URL de base de datos (en contenedor la provee compose; local usa el respaldo).
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesion SQLAlchemy por peticion."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() # Cierra la sesión luego de terminar la peti


def get_user_repository(session: Session = Depends(get_db)) -> UserRepository:
    """Construye el repositorio Postgres con la sesion de la peticion."""
    return PostgresUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    """Entrega el cifrador Bcrypt (sin estado)."""
    return BcryptPasswordHasher()


def get_token_service() -> TokenService:
    """Entrega el emisor JWT (lee el secreto del entorno)."""
    return JwtTokenService()


def get_register_user(
    repository: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
) -> RegisterUser:
    """Construye el caso de uso de registro."""
    return RegisterUser(repository=repository, hasher=hasher)


def get_login_user(
    repository: UserRepository = Depends(get_user_repository),
    hasher: PasswordHasher = Depends(get_password_hasher),
    tokens: TokenService = Depends(get_token_service),
) -> LoginUser:
    """Construye el caso de uso de login."""
    return LoginUser(repository=repository, hasher=hasher, tokens=tokens)


def get_promote_user(
    repository: UserRepository = Depends(get_user_repository),
) -> PromoteUser:
    """Construye el caso de uso de promocion."""
    return PromoteUser(repository=repository)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Valida el token Bearer y devuelve el usuario autenticado."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
    try:
        claims = jwt.decode(
            credentials.credentials,
            os.getenv("SECRET_KEY", ""),
            algorithms=["HS256"],
        )
        user_id = int(claims.get("sub", ""))
    except (JWTError, ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    """Exige rol ADMIN (403 si el usuario no lo tiene)."""
    if current.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return current
