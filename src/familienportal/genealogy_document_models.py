from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class GenealogyDocumentLink(Base):
    __tablename__ = "genealogy_document_links"
    __table_args__ = (UniqueConstraint("family_id", "person_handle", "provider", "external_ref", name="uq_genealogy_document_link"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    person_handle: Mapped[str] = mapped_column(String(128), index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    external_ref: Mapped[str] = mapped_column(String(700))
    title: Mapped[str] = mapped_column(String(240))
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
