from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from familienportal.database import Base

class TaskStatus(StrEnum):
    OPEN="open"
    IN_PROGRESS="in_progress"
    DONE="done"
    CANCELLED="cancelled"

class TaskPriority(StrEnum):
    LOW="low"
    NORMAL="normal"
    HIGH="high"
    URGENT="urgent"

class FamilyTask(Base):
    __tablename__="family_tasks"
    id:Mapped[UUID]=mapped_column(primary_key=True,default=uuid4)
    family_id:Mapped[UUID]=mapped_column(ForeignKey("families.id",ondelete="CASCADE"),index=True)
    household_id:Mapped[UUID|None]=mapped_column(ForeignKey("households.id",ondelete="SET NULL"),nullable=True,index=True)
    creator_user_id:Mapped[UUID|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True,index=True)
    assignee_user_id:Mapped[UUID|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"),nullable=True,index=True)
    title:Mapped[str]=mapped_column(String(240));description:Mapped[str|None]=mapped_column(Text,nullable=True)
    status:Mapped[str]=mapped_column(String(30),default=TaskStatus.OPEN.value,index=True)
    priority:Mapped[str]=mapped_column(String(20),default=TaskPriority.NORMAL.value,index=True)
    due_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True)
    completed_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True,index=True)
    recurrence:Mapped[str|None]=mapped_column(String(40),nullable=True);recurrence_interval:Mapped[int]=mapped_column(Integer,default=1)
    is_private:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),index=True)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc))
