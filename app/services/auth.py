from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationException,
    BadRequestException,
    ConflictException,
)
from app.core.messages import (
    EMAIL_ALREADY_REGISTERED,
    INACTIVE_USER,
    INCORRECT_CURRENT_PASSWORD,
    INVALID_CREDENTIALS,
    INVALID_TOKEN,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_password_dummy,
)
from app.models import RefreshToken, User
from app.models.enums import RevokeReason, UserRole
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: RefreshTokenRepository,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.settings = settings
        self.session_factory = session_factory

    async def _revoke_family_and_fail(self, user_id: int) -> None:
        if self.session_factory is not None:
            async with self.session_factory() as session, session.begin():
                repo = RefreshTokenRepository(session)
                await repo.revoke_all_for_user(user_id, RevokeReason.ROTATED)
        else:
            await self.token_repository.revoke_all_for_user(
                user_id, RevokeReason.ROTATED
            )
        raise AuthenticationException(INVALID_TOKEN)

    async def register(self, payload: UserCreate) -> User:
        async with self.user_repository.session.begin_nested():
            if await self.user_repository.get_by_email(payload.email) is not None:
                raise ConflictException(EMAIL_ALREADY_REGISTERED)
            hashed_pw = await run_in_threadpool(hash_password, payload.password)
            user = User(
                email=payload.email,
                full_name=payload.full_name,
                hashed_password=hashed_pw,
                role=UserRole.MEMBER,
                is_active=True,
                token_version=1,
            )
            try:
                return await self.user_repository.create(user)
            except IntegrityError:
                raise ConflictException(EMAIL_ALREADY_REGISTERED) from None

    async def _issue_tokens(self, user: User) -> TokenResponse:
        secret = self.settings.jwt_secret_key.get_secret_value()
        algorithm = self.settings.jwt_algorithm
        access_token = create_access_token(
            subject=user.id,
            secret_key=secret,
            algorithm=algorithm,
            expires_delta=timedelta(minutes=self.settings.access_token_expire_minutes),
            token_version=user.token_version,
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            secret_key=secret,
            algorithm=algorithm,
            expires_delta=timedelta(days=self.settings.refresh_token_expire_days),
        )
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        await self.token_repository.create(
            RefreshToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if user is None:
            await run_in_threadpool(verify_password_dummy, payload.password)
            raise AuthenticationException(INVALID_CREDENTIALS)
        is_valid = await run_in_threadpool(
            verify_password, payload.password, user.hashed_password
        )
        if not is_valid:
            raise AuthenticationException(INVALID_CREDENTIALS)
        if not user.is_active:
            raise AuthenticationException(INACTIVE_USER)
        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        secret = self.settings.jwt_secret_key.get_secret_value()
        algorithm = self.settings.jwt_algorithm
        user_id = decode_refresh_token(
            token=refresh_token,
            secret_key=secret,
            algorithm=algorithm,
        )
        token_hash = hash_token(refresh_token)
        token_record = await self.token_repository.get_by_token_hash(token_hash)
        if token_record is None:
            raise AuthenticationException(INVALID_TOKEN)

        # Reuse detection: only revoke family if token was ROTATED!
        if token_record.revoked_at is not None:
            if token_record.revoke_reason == RevokeReason.ROTATED:
                await self._revoke_family_and_fail(token_record.user_id)
            raise AuthenticationException(INVALID_TOKEN)

        now = datetime.now(UTC)
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            raise AuthenticationException(INVALID_TOKEN)

        user = await self.user_repository.get(user_id)
        if user is None:
            raise AuthenticationException(INVALID_TOKEN)
        if not user.is_active:
            raise AuthenticationException(INACTIVE_USER)

        revoked = await self.token_repository.revoke_active_by_hash(
            token_hash, now, reason=RevokeReason.ROTATED
        )
        if not revoked:
            await self._revoke_family_and_fail(user.id)

        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        secret = self.settings.jwt_secret_key.get_secret_value()
        algorithm = self.settings.jwt_algorithm
        decode_refresh_token(
            token=refresh_token,
            secret_key=secret,
            algorithm=algorithm,
        )
        token_hash = hash_token(refresh_token)
        now = datetime.now(UTC)
        revoked = await self.token_repository.revoke_active_by_hash(
            token_hash, now, reason=RevokeReason.LOGOUT
        )
        if not revoked:
            raise AuthenticationException(INVALID_TOKEN)

    async def get_current_user(self, token: str) -> User:
        payload = decode_access_token(
            token=token,
            secret_key=self.settings.jwt_secret_key.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
        )
        user_id = int(str(payload["sub"]))
        user = await self.user_repository.get(user_id)
        if user is None:
            raise AuthenticationException(INVALID_TOKEN)
        if not user.is_active:
            raise AuthenticationException(INACTIVE_USER)
        if payload.get("ver") != user.token_version:
            raise AuthenticationException(INVALID_TOKEN)
        return user

    async def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        is_valid = await run_in_threadpool(
            verify_password, payload.current_password, user.hashed_password
        )
        if not is_valid:
            raise BadRequestException(INCORRECT_CURRENT_PASSWORD)
        new_hashed_password = await run_in_threadpool(
            hash_password, payload.new_password
        )
        user.token_version += 1
        await self.user_repository.update(
            user,
            {
                "hashed_password": new_hashed_password,
                "token_version": user.token_version,
            },
        )
        await self.token_repository.revoke_all_for_user(
            user.id, reason=RevokeReason.PASSWORD_CHANGED
        )
