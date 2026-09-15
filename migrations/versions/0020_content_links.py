"""link notes and lists with tasks and calendar events

Revision ID: 0020
Revises: 0019
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("note_id", sa.Uuid(), nullable=True),
        sa.Column("list_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("(note_id IS NOT NULL) <> (list_id IS NOT NULL)", name="ck_content_link_one_source"),
        sa.CheckConstraint("(task_id IS NOT NULL) <> (event_id IS NOT NULL)", name="ck_content_link_one_target"),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["note_id"], ["family_notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["list_id"], ["family_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["family_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["calendar_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "note_id", "list_id", "task_id", "event_id", name="uq_content_link_target"),
    )
    for name in ("family_id", "kind", "note_id", "list_id", "task_id", "event_id", "created_by_user_id"):
        op.create_index(f"ix_content_links_{name}", "content_links", [name])


def downgrade() -> None:
    op.drop_table("content_links")
