"""Crea la tabla users con unicidad y rol (BR-8, BR-9, BR-13)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea users con UNIQUE en username y email_normalized mas CHECK de rol."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=20), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("email_normalized", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=5), server_default="USER", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('USER', 'ADMIN')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_normalized"),
        sa.UniqueConstraint("username"),
    )


def downgrade() -> None:
    """Elimina la tabla users."""
    op.drop_table("users")
