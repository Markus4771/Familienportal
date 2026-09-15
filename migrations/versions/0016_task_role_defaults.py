"""apply task permissions to existing system roles

Revision ID: 0016
Revises: 0015
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

TASK_DEFAULTS: dict[str, set[str]] = {
    "Administrator": {"*"},
    "Erwachsene": {"tasks.read", "tasks.create", "tasks.edit", "tasks.assign", "tasks.complete", "tasks.delete", "tasks.manage"},
    "Kind": {"tasks.read", "tasks.create", "tasks.edit", "tasks.complete"},
    "Gast": {"tasks.read"},
}


def _split_permissions(value: str | None) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


def upgrade() -> None:
    connection = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("permissions", sa.Text()),
        sa.column("system_role", sa.Boolean()),
    )
    rows = connection.execute(
        sa.select(roles.c.id, roles.c.name, roles.c.permissions).where(roles.c.system_role.is_(True))
    ).mappings()
    for row in rows:
        defaults = TASK_DEFAULTS.get(row["name"])
        if not defaults:
            continue
        current = _split_permissions(row["permissions"])
        if "*" in current:
            continue
        merged = current | defaults
        if merged != current:
            connection.execute(
                roles.update().where(roles.c.id == row["id"]).values(permissions=",".join(sorted(merged)))
            )


def downgrade() -> None:
    # Existing installations may have customized task permissions after upgrade.
    # Removing them automatically would destroy administrator choices, so this
    # data migration is intentionally non-destructive on downgrade.
    pass
