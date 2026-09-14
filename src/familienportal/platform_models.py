from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from familienportal.database import Base


class ModuleState(Base):
    __tablename__ = "module_states"
    __table_args__ = (UniqueConstraint("family_id", "module_key", name="uq_module_state_family_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    module_key: Mapped[str] = mapped_column(String(80), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConnectorState(Base):
    __tablename__ = "connector_states"
    __table_args__ = (UniqueConstraint("family_id", "connector_key", name="uq_connector_state_family_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    connector_key: Mapped[str] = mapped_column(String(80), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    username: Mapped[str | None] = mapped_column(String(320), nullable=True)
    secret_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    health_status: Mapped[str] = mapped_column(String(40), default="not_checked")
    health_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    health_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FamilySetting(Base):
    __tablename__ = "family_settings"
    __table_args__ = (UniqueConstraint("family_id", "setting_key", name="uq_family_setting_key"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id", ondelete="CASCADE"), index=True)
    setting_key: Mapped[str] = mapped_column(String(120), index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
