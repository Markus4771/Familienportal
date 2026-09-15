from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.nextcloud import NextcloudClient, NextcloudError
from familienportal.nextcloud_models import NextcloudFamilyFolder


def family_roots(db: Session, family_id: UUID, client: NextcloudClient) -> list[str]:
    rows = db.scalars(select(NextcloudFamilyFolder).where(NextcloudFamilyFolder.family_id == family_id)).all()
    roots: list[str] = []
    for row in rows:
        try:
            root = client._safe_relative_path(row.path)
        except NextcloudError:
            continue
        if root not in roots:
            roots.append(root)
    return roots


def path_in_roots(client: NextcloudClient, relative_path: str, roots: list[str]) -> str:
    path = client._safe_relative_path(relative_path)
    for root in roots:
        if path == root or path.startswith(root + "/"):
            return path
    raise NextcloudError("Der Dateipfad liegt außerhalb der freigegebenen Familienordner.")


def picker_path(client: NextcloudClient, requested_path: str, roots: list[str]) -> str:
    if not roots:
        raise NextcloudError("Für diese Familie ist noch kein Nextcloud-Familienordner konfiguriert.")
    if not requested_path:
        return roots[0]
    return path_in_roots(client, requested_path, roots)
