from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.messages import NOT_AUTHENTICATED, PERMISSION_DENIED
from app.db.session import get_session
from app.models import User
from app.models.enums import UserRole
from app.repositories.project import ProjectRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthService
from app.services.cache import TaskCacheService
from app.services.email import EmailService, get_email_service
from app.services.project import ProjectService
from app.services.task import TaskService
from app.services.user import UserService
from app.services.workspace import WorkspaceService

SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_refresh_token_repository(session: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_auth_service(
    request: Request,
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    token_repository: Annotated[
        RefreshTokenRepository, Depends(get_refresh_token_repository)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    session_factory = getattr(request.app.state, "session_factory", None)
    return AuthService(
        user_repository, token_repository, settings, session_factory=session_factory
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repository)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: AuthServiceDep,
) -> User:
    if credentials is None or not credentials.credentials.strip():
        raise AuthenticationException(NOT_AUTHENTICATED)
    return await service.get_current_user(credentials.credentials.strip())


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def role_checker(current_user: CurrentUserDep) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(PERMISSION_DENIED)
        return current_user

    return role_checker


AdminUserDep = Annotated[User, Depends(require_roles(UserRole.ADMIN))]


def get_workspace_repository(session: SessionDep) -> WorkspaceRepository:
    return WorkspaceRepository(session)


def get_workspace_service(
    repository: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
) -> WorkspaceService:
    return WorkspaceService(repository)


def get_task_cache_service() -> TaskCacheService:
    return TaskCacheService(redis_client=None)


def get_project_repository(session: SessionDep) -> ProjectRepository:
    return ProjectRepository(session)


def get_project_service(
    repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    workspace_repository: Annotated[
        WorkspaceRepository, Depends(get_workspace_repository)
    ],
    cache_service: Annotated[TaskCacheService, Depends(get_task_cache_service)],
) -> ProjectService:
    return ProjectService(repository, workspace_repository, cache_service)


def get_task_repository(session: SessionDep) -> TaskRepository:
    return TaskRepository(session)


def get_task_service(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
    workspace_repository: Annotated[
        WorkspaceRepository, Depends(get_workspace_repository)
    ],
    cache_service: Annotated[TaskCacheService, Depends(get_task_cache_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> TaskService:
    return TaskService(repository, workspace_repository, cache_service, email_service)


__all__ = [
    "AdminUserDep",
    "AuthServiceDep",
    "CurrentUserDep",
    "SessionDep",
    "Settings",
    "UserServiceDep",
    "bearer_scheme",
    "get_auth_service",
    "get_current_user",
    "get_db_session",
    "get_email_service",
    "get_project_repository",
    "get_project_service",
    "get_refresh_token_repository",
    "get_session",
    "get_settings",
    "get_task_cache_service",
    "get_task_repository",
    "get_task_service",
    "get_user_repository",
    "get_user_service",
    "get_workspace_repository",
    "get_workspace_service",
    "require_roles",
]

get_db_session = get_session
