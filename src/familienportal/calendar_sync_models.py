from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class CalendarSyncBinding(Base):
    __tablename__ = "calendar_sync_bindings"
    __table_args__ = (UniqueConstraint("family_id", "calendar_id", name="uq_calendar_sync_binding"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    calendar_id: Mapped[UUID] = mapped_column(ForeignKey("calendars.id", ondelete="CASCADE"), index=True)
    remote_href: Mapped[str] = mapped_column(String(800))
    remote_name: Mapped[str | None] = mapped_column(String(240), nullable=True)
    sync_token: Mapped[str | None] = mapped_column(String(800), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str] = mapped_column(String(40), default="never")
    last_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CalendarEventSyncState(Base):
    __tablename__ = "calendar_event_sync_states"
    __table_args__ = (UniqueConstraint("event_id", name="uq_calendar_event_sync_state"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("calendar_events.id", ondelete="CASCADE"), index=True)
    binding_id: Mapped[UUID] = mapped_column(ForeignKey("calendar_sync_bindings.id", ondelete="CASCADE"), index=True)
    remote_href: Mapped[str] = mapped_column(String(1000))
    remote_etag: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remote_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_local_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
