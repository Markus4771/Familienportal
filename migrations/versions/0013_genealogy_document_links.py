from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "genealogy_document_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("person_handle", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_ref", sa.String(700), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family_id", "person_handle", "provider", "external_ref", name="uq_genealogy_document_link"),
    )
    op.create_index("ix_genealogy_document_links_family_id", "genealogy_document_links", ["family_id"])
    op.create_index("ix_genealogy_document_links_person_handle", "genealogy_document_links", ["person_handle"])
    op.create_index("ix_genealogy_document_links_provider", "genealogy_document_links", ["provider"])


def downgrade() -> None:
    op.drop_table("genealogy_document_links")
