"""CalDAV synchronization state.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calendar_sync_bindings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("calendar_id", sa.Uuid(), nullable=False),
        sa.Column("remote_href", sa.String(800), nullable=False),
        sa.Column("remote_name", sa.String(240), nullable=True),
        sa.Column("sync_token", sa.String(800), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(40), nullable=False),
        sa.Column("last_message", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["calendar_id"], ["calendars.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "calendar_id", name="uq_calendar_sync_binding"),
    )
    op.create_index("ix_calendar_sync_bindings_family_id", "calendar_sync_bindings", ["family_id"])
    op.create_index("ix_calendar_sync_bindings_calendar_id", "calendar_sync_bindings", ["calendar_id"])

    op.create_table(
        "calendar_event_sync_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("binding_id", sa.Uuid(), nullable=False),
        sa.Column("remote_href", sa.String(1000), nullable=False),
        sa.Column("remote_etag", sa.String(500), nullable=True),
        sa.Column("remote_modified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_local_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_remote", sa.Boolean(), nullable=False),
        sa.Column("conflict", sa.Boolean(), nullable=False),
        sa.Column("conflict_message", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["calendar_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["binding_id"], ["calendar_sync_bindings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_calendar_event_sync_state"),
    )
    op.create_index("ix_calendar_event_sync_states_event_id", "calendar_event_sync_states", ["event_id"])
    op.create_index("ix_calendar_event_sync_states_binding_id", "calendar_event_sync_states", ["binding_id"])


def downgrade() -> None:
    op.drop_table("calendar_event_sync_states")
    op.drop_table("calendar_sync_bindings")
