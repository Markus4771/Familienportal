"""add family notes

Revision ID: 0017
Revises: 0016
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "family_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_family_notes_family_id", "family_notes", ["family_id"])
    op.create_index("ix_family_notes_household_id", "family_notes", ["household_id"])
    op.create_index("ix_family_notes_owner_user_id", "family_notes", ["owner_user_id"])
    op.create_index("ix_family_notes_is_private", "family_notes", ["is_private"])
    op.create_index("ix_family_notes_archived_at", "family_notes", ["archived_at"])
    op.create_index("ix_family_notes_created_at", "family_notes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_family_notes_created_at", table_name="family_notes")
    op.drop_index("ix_family_notes_archived_at", table_name="family_notes")
    op.drop_index("ix_family_notes_is_private", table_name="family_notes")
    op.drop_index("ix_family_notes_owner_user_id", table_name="family_notes")
    op.drop_index("ix_family_notes_household_id", table_name="family_notes")
    op.drop_index("ix_family_notes_family_id", table_name="family_notes")
    op.drop_table("family_notes")
