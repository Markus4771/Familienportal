from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class GrampsUserMapping(Base):
    __tablename__ = "gramps_user_mappings"
    __table_args__ = (UniqueConstraint("family_id", "user_id", name="uq_gramps_user_mapping_user"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    gramps_username: Mapped[str | None] = mapped_column(String(320), nullable=True)
    gramps_role: Mapped[str] = mapped_column(String(40), default="Guest")
    person_handle: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
