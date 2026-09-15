from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class ContentShareKind(StrEnum):
    NOTE = "note"
    LIST = "list"


class ContentShare(Base):
    __tablename__ = "content_shares"
    __table_args__ = (
        CheckConstraint("(note_id IS NOT NULL) <> (list_id IS NOT NULL)", name="ck_content_share_one_source"),
        CheckConstraint("(user_id IS NOT NULL) <> (household_id IS NOT NULL)", name="ck_content_share_one_target"),
        UniqueConstraint("note_id", "user_id", name="uq_content_share_note_user"),
        UniqueConstraint("note_id", "household_id", name="uq_content_share_note_household"),
        UniqueConstraint("list_id", "user_id", name="uq_content_share_list_user"),
        UniqueConstraint("list_id", "household_id", name="uq_content_share_list_household"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    note_id: Mapped[UUID | None] = mapped_column(ForeignKey("family_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    list_id: Mapped[UUID | None] = mapped_column(ForeignKey("family_lists.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    household_id: Mapped[UUID | None] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
