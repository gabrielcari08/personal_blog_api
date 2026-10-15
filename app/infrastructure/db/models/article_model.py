"""Modelo ORM de articulos (mapeo fisico de PostgreSQL)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class ArticleModel(Base):
    """Fila de la tabla articles (autoria inmutable y tiempo de auditoria)."""

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint(
            "char_length(title) BETWEEN 8 AND 20", name="ck_articles_title_length"
        ),
        CheckConstraint(
            "char_length(text) BETWEEN 10 AND 300", name="ck_articles_text_length"
        ),
        Index("ix_articles_user_id", "user_id"),
        Index("ix_articles_created_desc", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(20), nullable=False)
    # Autor asignado por el sistema; sin transferencia posterior.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Tiempo de creacion con zona horaria, igual que en usuarios.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
