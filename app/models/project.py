from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PROJECT_NAME_MAX_LENGTH
from app.db.base import Base, CreatedAtMixin, enum_column
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.label import Label
    from app.models.task import Task
    from app.models.workspace import Workspace


class Project(CreatedAtMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(PROJECT_NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = enum_column(
        ProjectStatus, "project_status", ProjectStatus.ACTIVE
    )

    workspace: Mapped[Workspace] = relationship(back_populates="projects", lazy="raise")
    tasks: Mapped[list[Task]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    labels: Mapped[list[Label]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
