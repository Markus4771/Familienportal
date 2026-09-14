from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("job_deliveries", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("job_deliveries", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("job_deliveries", "last_attempt_at")
    op.drop_column("job_deliveries", "attempts")
