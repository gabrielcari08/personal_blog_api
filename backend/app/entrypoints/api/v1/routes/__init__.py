"""Rutas de la API v1."""

from app.entrypoints.api.v1.routes.user_router import router as user_router

__all__ = ["user_router"]
