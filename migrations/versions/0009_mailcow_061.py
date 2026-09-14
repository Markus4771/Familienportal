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
    op.create_table(
        "mailcow_user_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("mailbox", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "user_id", name="uq_mailcow_mapping_family_user"),
        sa.UniqueConstraint("family_id", "mailbox", name="uq_mailcow_mapping_family_mailbox"),
    )
    op.create_index("ix_mailcow_user_mappings_family_id", "mailcow_user_mappings", ["family_id"])
    op.create_index("ix_mailcow_user_mappings_user_id", "mailcow_user_mappings", ["user_id"])
    op.create_index("ix_mailcow_user_mappings_mailbox", "mailcow_user_mappings", ["mailbox"])


def downgrade() -> None:
    op.drop_table("mailcow_user_mappings")
    op.drop_column("job_deliveries", "last_attempt_at")
    op.drop_column("job_deliveries", "attempts")
