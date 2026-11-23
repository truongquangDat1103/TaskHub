from fastapi import APIRouter, Response, status

from app.core.dependencies import AuthServiceDep, CurrentUserDep, UserServiceDep
from app.core.messages import (
    INCORRECT_CURRENT_PASSWORD,
    NOT_AUTHENTICATED,
)
from app.models import User
from app.schemas.auth import ChangePasswordRequest
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
    responses={401: {"description": NOT_AUTHENTICATED}},
)
async def get_current_user_profile(current_user: CurrentUserDep) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
    responses={401: {"description": NOT_AUTHENTICATED}},
)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: CurrentUserDep,
    service: UserServiceDep,
) -> User:
    return await service.update_profile(current_user, payload)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password for current user",
    responses={
        400: {"description": INCORRECT_CURRENT_PASSWORD},
        401: {"description": NOT_AUTHENTICATED},
    },
)
async def change_user_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    service: AuthServiceDep,
) -> Response:
    await service.change_password(current_user, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
