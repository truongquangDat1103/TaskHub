from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    PASSWORD_HASH_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
)
from app.db.base import Base, CreatedAtMixin, enum_column
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken
    from app.models.workspace import Workspace, WorkspaceMember


class User(CreatedAtMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(USER_EMAIL_MAX_LENGTH), unique=True)
    full_name: Mapped[str] = mapped_column(String(USER_NAME_MAX_LENGTH))
    hashed_password: Mapped[str] = mapped_column(String(PASSWORD_HASH_MAX_LENGTH))
    role: Mapped[UserRole] = enum_column(UserRole, "user_role", UserRole.MEMBER)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    token_version: Mapped[int] = mapped_column(Integer, server_default="1", default=1)

    owned_workspaces: Mapped[list[Workspace]] = relationship(
        back_populates="owner", lazy="raise", passive_deletes="all"
    )
    memberships: Mapped[list[WorkspaceMember]] = relationship(
        back_populates="user", lazy="raise", passive_deletes="all"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", lazy="raise", passive_deletes="all"
    )
