"""Platform management state.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "module_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("module_key", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "module_key", name="uq_module_state_family_key"),
    )
    op.create_index("ix_module_states_family_id", "module_states", ["family_id"])
    op.create_index("ix_module_states_module_key", "module_states", ["module_key"])

    op.create_table(
        "connector_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("connector_key", sa.String(80), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("health_status", sa.String(40), nullable=False),
        sa.Column("health_message", sa.String(500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "connector_key", name="uq_connector_state_family_key"),
    )
    op.create_index("ix_connector_states_family_id", "connector_states", ["family_id"])
    op.create_index("ix_connector_states_connector_key", "connector_states", ["connector_key"])

    op.create_table(
        "family_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("setting_key", sa.String(120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "setting_key", name="uq_family_setting_key"),
    )
    op.create_index("ix_family_settings_family_id", "family_settings", ["family_id"])
    op.create_index("ix_family_settings_setting_key", "family_settings", ["setting_key"])


def downgrade() -> None:
    op.drop_table("family_settings")
    op.drop_table("connector_states")
    op.drop_table("module_states")
