"""Nextcloud mappings and family folders.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nextcloud_user_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("nextcloud_user_id", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "user_id", name="uq_nc_user_mapping_user"),
        sa.UniqueConstraint("family_id", "nextcloud_user_id", name="uq_nc_user_mapping_remote"),
    )
    op.create_index("ix_nextcloud_user_mappings_family_id", "nextcloud_user_mappings", ["family_id"])
    op.create_index("ix_nextcloud_user_mappings_user_id", "nextcloud_user_mappings", ["user_id"])
    op.create_index("ix_nextcloud_user_mappings_nextcloud_user_id", "nextcloud_user_mappings", ["nextcloud_user_id"])

    op.create_table(
        "nextcloud_group_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("nextcloud_group_id", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "target_type", "target_id", name="uq_nc_group_mapping_target"),
    )
    op.create_index("ix_nextcloud_group_mappings_family_id", "nextcloud_group_mappings", ["family_id"])
    op.create_index("ix_nextcloud_group_mappings_nextcloud_group_id", "nextcloud_group_mappings", ["nextcloud_group_id"])

    op.create_table(
        "nextcloud_family_folders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "path", name="uq_nc_family_folder_path"),
    )
    op.create_index("ix_nextcloud_family_folders_family_id", "nextcloud_family_folders", ["family_id"])
    op.create_index("ix_nextcloud_family_folders_household_id", "nextcloud_family_folders", ["household_id"])


def downgrade() -> None:
    op.drop_table("nextcloud_family_folders")
    op.drop_table("nextcloud_group_mappings")
    op.drop_table("nextcloud_user_mappings")
