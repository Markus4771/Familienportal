"""Calendar UI enhancements.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("calendars", sa.Column("color", sa.String(length=20), nullable=False, server_default="#0d6efd"))


def downgrade() -> None:
    op.drop_column("calendars", "color")
