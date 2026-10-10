"""Seeds de la base de datos."""

from app.infrastructure.db.seeds.admin_seed import ensure_admin_exists

__all__ = ["ensure_admin_exists"]
