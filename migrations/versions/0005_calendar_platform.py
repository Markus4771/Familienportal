"""Calendar platform.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calendars",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "slug", name="uq_calendar_family_slug"),
    )
    op.create_index("ix_calendars_family_id", "calendars", ["family_id"])
    op.create_index("ix_calendars_owner_user_id", "calendars", ["owner_user_id"])
    op.create_index("ix_calendars_household_id", "calendars", ["household_id"])

    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("calendar_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("recurrence_rule", sa.String(500), nullable=True),
        sa.Column("reminder_minutes", sa.Integer(), nullable=True),
        sa.Column("external_uid", sa.String(255), nullable=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["calendar_id"], ["calendars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_events_family_id", "calendar_events", ["family_id"])
    op.create_index("ix_calendar_events_calendar_id", "calendar_events", ["calendar_id"])
    op.create_index("ix_calendar_events_starts_at", "calendar_events", ["starts_at"])
    op.create_index("ix_calendar_events_ends_at", "calendar_events", ["ends_at"])
    op.create_index("ix_calendar_events_external_uid", "calendar_events", ["external_uid"])

    op.create_table(
        "birthdays",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "name", "birth_date", name="uq_birthday_family_name_date"),
    )
    op.create_index("ix_birthdays_family_id", "birthdays", ["family_id"])
    op.create_index("ix_birthdays_user_id", "birthdays", ["user_id"])


def downgrade() -> None:
    op.drop_table("birthdays")
    op.drop_table("calendar_events")
    op.drop_table("calendars")
