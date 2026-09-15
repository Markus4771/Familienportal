"""harden content links

Revision ID: 0023
Revises: 0022
"""
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Service-level validation remains authoritative across SQLite/PostgreSQL.
    # Partial indexes prevent logical duplicates despite NULL semantics.
    op.create_index("uq_content_link_note_task", "content_links", ["family_id", "note_id", "task_id"], unique=True, postgresql_where="note_id IS NOT NULL AND task_id IS NOT NULL", sqlite_where="note_id IS NOT NULL AND task_id IS NOT NULL")
    op.create_index("uq_content_link_note_event", "content_links", ["family_id", "note_id", "event_id"], unique=True, postgresql_where="note_id IS NOT NULL AND event_id IS NOT NULL", sqlite_where="note_id IS NOT NULL AND event_id IS NOT NULL")
    op.create_index("uq_content_link_list_task", "content_links", ["family_id", "list_id", "task_id"], unique=True, postgresql_where="list_id IS NOT NULL AND task_id IS NOT NULL", sqlite_where="list_id IS NOT NULL AND task_id IS NOT NULL")
    op.create_index("uq_content_link_list_event", "content_links", ["family_id", "list_id", "event_id"], unique=True, postgresql_where="list_id IS NOT NULL AND event_id IS NOT NULL", sqlite_where="list_id IS NOT NULL AND event_id IS NOT NULL")


def downgrade() -> None:
    for name in ("uq_content_link_list_event", "uq_content_link_list_task", "uq_content_link_note_event", "uq_content_link_note_task"):
        op.drop_index(name, table_name="content_links")
