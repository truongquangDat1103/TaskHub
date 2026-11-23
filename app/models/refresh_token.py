from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import REFRESH_TOKEN_HASH_LENGTH
from app.db.base import Base, CreatedAtMixin, enum_column
from app.models.enums import RevokeReason

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(CreatedAtMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(REFRESH_TOKEN_HASH_LENGTH), unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    revoke_reason: Mapped[RevokeReason | None] = enum_column(
        RevokeReason, "revoke_reason", default=None
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens", lazy="raise")
