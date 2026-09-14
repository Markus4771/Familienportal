from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class NextcloudUserMapping(Base):
    __tablename__ = "nextcloud_user_mappings"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_nc_user_mapping_user"),
        UniqueConstraint("family_id", "nextcloud_user_id", name="uq_nc_user_mapping_remote"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    nextcloud_user_id: Mapped[str] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class NextcloudGroupMapping(Base):
    __tablename__ = "nextcloud_group_mappings"
    __table_args__ = (UniqueConstraint("family_id", "target_type", "target_id", name="uq_nc_group_mapping_target"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[UUID] = mapped_column(index=True)
    nextcloud_group_id: Mapped[str] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class NextcloudFamilyFolder(Base):
    __tablename__ = "nextcloud_family_folders"
    __table_args__ = (UniqueConstraint("family_id", "path", name="uq_nc_family_folder_path"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    household_id: Mapped[UUID | None] = mapped_column(ForeignKey("households.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
