"""Connector credential references and health timestamps.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("connector_states", sa.Column("username", sa.String(length=320), nullable=True))
    op.add_column("connector_states", sa.Column("secret_reference", sa.String(length=160), nullable=True))
    op.add_column("connector_states", sa.Column("health_checked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("connector_states", "health_checked_at")
    op.drop_column("connector_states", "secret_reference")
    op.drop_column("connector_states", "username")
