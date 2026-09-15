from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class ContentLinkKind(StrEnum):
    NOTE_TASK = "note_task"
    NOTE_EVENT = "note_event"
    LIST_TASK = "list_task"
    LIST_EVENT = "list_event"


class ContentLink(Base):
    __tablename__ = "content_links"
    __table_args__ = (UniqueConstraint("kind", "note_id", "list_id", "task_id", "event_id", name="uq_content_link_target"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    note_id: Mapped[UUID | None] = mapped_column(ForeignKey("family_notes.id", ondelete="CASCADE"), nullable=True, index=True)
    list_id: Mapped[UUID | None] = mapped_column(ForeignKey("family_lists.id", ondelete="CASCADE"), nullable=True, index=True)
    task_id: Mapped[UUID | None] = mapped_column(ForeignKey("family_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def expected_kind(self) -> str | None:
        if self.note_id is not None and self.list_id is None and self.task_id is not None and self.event_id is None:
            return ContentLinkKind.NOTE_TASK.value
        if self.note_id is not None and self.list_id is None and self.event_id is not None and self.task_id is None:
            return ContentLinkKind.NOTE_EVENT.value
        if self.list_id is not None and self.note_id is None and self.task_id is not None and self.event_id is None:
            return ContentLinkKind.LIST_TASK.value
        if self.list_id is not None and self.note_id is None and self.event_id is not None and self.task_id is None:
            return ContentLinkKind.LIST_EVENT.value
        return None

    def targets_are_valid(self) -> bool:
        """Validate the one-source/one-target shape; kept compatible with 0.11 callers."""
        return self.expected_kind() is not None

    def kind_is_valid(self) -> bool:
        """Additionally validate that the persisted kind matches the source/target shape."""
        expected = self.expected_kind()
        return expected is not None and self.kind == expected
