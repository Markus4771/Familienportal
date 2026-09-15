"""task archive

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa
revision="0015";down_revision="0014";branch_labels=None;depends_on=None

def upgrade():
    op.add_column("family_tasks",sa.Column("archived_at",sa.DateTime(timezone=True),nullable=True))
    op.create_index("ix_family_tasks_archived_at","family_tasks",["archived_at"])

def downgrade():
    op.drop_index("ix_family_tasks_archived_at",table_name="family_tasks")
    op.drop_column("family_tasks","archived_at")
