from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import WORKSPACE_NAME_MAX_LENGTH
from app.db.base import Base, CreatedAtMixin, enum_column
from app.models.enums import WorkspaceRole

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Workspace(CreatedAtMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(WORKSPACE_NAME_MAX_LENGTH))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )

    owner: Mapped[User] = relationship(back_populates="owned_workspaces", lazy="raise")
    members: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[WorkspaceRole] = enum_column(
        WorkspaceRole, "workspace_role", WorkspaceRole.VIEWER
    )

    workspace: Mapped[Workspace] = relationship(back_populates="members", lazy="raise")
    user: Mapped[User] = relationship(back_populates="memberships", lazy="raise")
