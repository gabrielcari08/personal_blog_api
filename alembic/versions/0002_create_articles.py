"""Crea la tabla articles con autoria, longitud y tiempo de auditoria."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_articles"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea articles con FK a users, CHECKs de longitud e indices de orden y autor."""
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 8 AND 20", name="ck_articles_title_length"
        ),
        sa.CheckConstraint(
            "char_length(text) BETWEEN 10 AND 300", name="ck_articles_text_length"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_articles_user_id", "articles", ["user_id"])
    op.create_index("ix_articles_created_desc", "articles", ["created_at", "id"])


def downgrade() -> None:
    """Elimina los indices y la tabla articles (users queda intacta)."""
    op.drop_index("ix_articles_created_desc", table_name="articles")
    op.drop_index("ix_articles_user_id", table_name="articles")
    op.drop_table("articles")
