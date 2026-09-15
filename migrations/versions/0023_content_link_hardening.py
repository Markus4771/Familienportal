"""harden content links

Revision ID: 0023
Revises: 0022
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    indexes = (
        ("uq_content_link_note_task", ["family_id", "note_id", "task_id"], "note_id IS NOT NULL AND task_id IS NOT NULL"),
        ("uq_content_link_note_event", ["family_id", "note_id", "event_id"], "note_id IS NOT NULL AND event_id IS NOT NULL"),
        ("uq_content_link_list_task", ["family_id", "list_id", "task_id"], "list_id IS NOT NULL AND task_id IS NOT NULL"),
        ("uq_content_link_list_event", ["family_id", "list_id", "event_id"], "list_id IS NOT NULL AND event_id IS NOT NULL"),
    )
    for name, columns, predicate in indexes:
        where = sa.text(predicate)
        op.create_index(name, "content_links", columns, unique=True, postgresql_where=where, sqlite_where=where)


def downgrade() -> None:
    for name in ("uq_content_link_list_event", "uq_content_link_list_task", "uq_content_link_note_event", "uq_content_link_note_task"):
        op.drop_index(name, table_name="content_links")
