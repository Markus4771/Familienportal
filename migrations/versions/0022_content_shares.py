"""targeted shares for notes and lists

Revision ID: 0022
Revises: 0021
"""
from alembic import op
import sqlalchemy as sa

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_shares",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("family_id", sa.Uuid(), sa.ForeignKey("families.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("note_id", sa.Uuid(), sa.ForeignKey("family_notes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("list_id", sa.Uuid(), sa.ForeignKey("family_lists.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("household_id", sa.Uuid(), sa.ForeignKey("households.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("(note_id IS NOT NULL) <> (list_id IS NOT NULL)", name="ck_content_share_one_source"),
        sa.CheckConstraint("(user_id IS NOT NULL) <> (household_id IS NOT NULL)", name="ck_content_share_one_target"),
        sa.UniqueConstraint("note_id", "user_id", name="uq_content_share_note_user"),
        sa.UniqueConstraint("note_id", "household_id", name="uq_content_share_note_household"),
        sa.UniqueConstraint("list_id", "user_id", name="uq_content_share_list_user"),
        sa.UniqueConstraint("list_id", "household_id", name="uq_content_share_list_household"),
    )
    for column in ("family_id", "kind", "note_id", "list_id", "user_id", "household_id"):
        op.create_index(f"ix_content_shares_{column}", "content_shares", [column])


def downgrade() -> None:
    op.drop_table("content_shares")
