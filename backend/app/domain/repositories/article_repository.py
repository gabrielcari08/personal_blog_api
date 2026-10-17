"""Contrato del repositorio de articulos (inversion de dependencias)."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.article import Article


class ArticleRepository(ABC):
    """Define la persistencia de articulos sin depender de infraestructura."""

    # Metodos de consulta (get_by... y listado).
    @abstractmethod
    def get_by_id(self, article_id: int) -> Optional[Article]:
        """Busca un articulo por su identificador opaco."""
        raise NotImplementedError

    @abstractmethod
    def list_all_desc(self) -> list[Article]:
        """Lista todos los articulos de mas reciente a mas antiguo (sin paginacion)."""
        raise NotImplementedError

    # Metodos de persistencia y modificación.
    @abstractmethod
    def save(self, article: Article) -> Article:
        """Guarda un articulo nuevo y lo devuelve con id y tiempo asignados."""
        raise NotImplementedError

    @abstractmethod
    def update(self, article: Article) -> Article:
        """Actualiza titulo y texto de un articulo existente y lo devuelve."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, article_id: int) -> None:
        """Elimina definitivamente un articulo existente."""
        raise NotImplementedError
