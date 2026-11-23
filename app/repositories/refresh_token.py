from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RevokeReason
from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return await self.session.scalar(statement)

    async def revoke_all_for_user(
        self, user_id: int, reason: RevokeReason | None = None
    ) -> None:
        values: dict[str, Any] = {"revoked_at": datetime.now(UTC)}
        if reason is not None:
            values["revoke_reason"] = reason
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(**values)
        )
        await self.session.execute(statement)
        await self.session.flush()

    async def revoke_active_by_hash(
        self,
        token_hash: str,
        revoked_at: datetime,
        reason: RevokeReason | None = None,
    ) -> bool:
        values: dict[str, Any] = {"revoked_at": revoked_at}
        if reason is not None:
            values["revoke_reason"] = reason
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(**values)
        )
        result = await self.session.execute(statement)
        await self.session.flush()
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount and rowcount > 0)
