"""Seed idempotente del administrador inicial (solo desde entorno)."""

import os
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dtos.user_dtos import RegisterInput
from app.domain.entities.user import User
from app.domain.services.password_hasher_service import PasswordHasher
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.repositories.postgres_user_repository import (
    PostgresUserRepository,
)

SeedResult = Literal["created", "already_exists"]


def ensure_admin_exists(session: Session, hasher: PasswordHasher) -> SeedResult:
    """Crea el ADMIN inicial desde el entorno si no existe (idempotente)."""
    username = os.getenv("ADMIN_USERNAME", "")
    email = os.getenv("ADMIN_EMAIL", "")
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not email or not password:
        raise ValueError("ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD are required.")

    # Valida con las mismas reglas del registro (formato y longitud de clave).
    checked = RegisterInput(username=username, email=email, password=password)
    normalized = str(checked.email).strip().lower()

    repository = PostgresUserRepository(session)
    if repository.get_by_email_normalized(normalized) is not None:
        return "already_exists"
    admin_exists = (
        session.scalar(
            select(UserModel.id).where(UserModel.role == "ADMIN").limit(1)
        )
        is not None
    )
    if admin_exists:
        return "already_exists"

    # La entidad valida username y rol; nunca se registra la clave.
    admin = User(
        username=checked.username,
        email=str(checked.email).strip(),
        password_hash=hasher.hash(checked.password),
        role="ADMIN",
    )
    repository.save(admin)
    return "created"
