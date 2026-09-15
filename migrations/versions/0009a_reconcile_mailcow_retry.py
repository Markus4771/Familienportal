"""Reconcile installations affected by the former duplicate revision 0009.

Revision ID: 0009a
Revises: 0009

Older development installations may have applied either the reminder-retry
variant or the Mailcow variant of revision 0009.  This migration makes both
states converge before the security migrations continue.
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0009a"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    delivery_columns = {column["name"] for column in inspector.get_columns("job_deliveries")}
    if "attempts" not in delivery_columns:
        op.add_column("job_deliveries", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    if "last_attempt_at" not in delivery_columns:
        op.add_column("job_deliveries", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))

    if "mailcow_user_mappings" not in tables:
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
    # 0009a only reconciles legacy states. Objects belong logically to 0009 and
    # are removed by the 0009 downgrade, so no destructive action is needed here.
    pass
