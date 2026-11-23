from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import TASK_TITLE_MAX_LENGTH
from app.db.base import Base, CreatedAtMixin, enum_column
from app.models.enums import TaskPriority, TaskStatus

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.label import Label
    from app.models.project import Project
    from app.models.user import User


task_labels = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "label_id",
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Task(CreatedAtMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(TASK_TITLE_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = enum_column(TaskStatus, "task_status", TaskStatus.TODO)
    priority: Mapped[TaskPriority] = enum_column(
        TaskPriority, "task_priority", TaskPriority.MEDIUM
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )

    project: Mapped[Project] = relationship(back_populates="tasks", lazy="raise")
    assignee: Mapped[User | None] = relationship(
        foreign_keys=[assignee_id], lazy="raise"
    )
    creator: Mapped[User] = relationship(foreign_keys=[created_by], lazy="raise")
    labels: Mapped[list[Label]] = relationship(
        secondary=task_labels,
        back_populates="tasks",
        passive_deletes=True,
        lazy="raise",
    )
    comments: Mapped[list[Comment]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
