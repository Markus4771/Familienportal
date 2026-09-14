from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "login_throttles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("identifier_hash", sa.String(64), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("identifier_hash"),
    )
    op.create_index("ix_login_throttles_identifier_hash", "login_throttles", ["identifier_hash"])
    op.create_index("ix_login_throttles_locked_until", "login_throttles", ["locked_until"])


def downgrade() -> None:
    op.drop_table("login_throttles")
