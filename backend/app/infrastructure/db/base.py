"""Base declarativa de los modelos de infraestructura."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base de la que heredan todos los modelos ORM."""

    pass
