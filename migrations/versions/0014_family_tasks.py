from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("creator_user_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence", sa.String(40), nullable=True),
        sa.Column("recurrence_interval", sa.Integer(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("family_id", "household_id", "creator_user_id", "assignee_user_id", "status", "priority", "due_at", "created_at"):
        op.create_index(f"ix_family_tasks_{column}", "family_tasks", [column])


def downgrade() -> None:
    op.drop_table("family_tasks")
