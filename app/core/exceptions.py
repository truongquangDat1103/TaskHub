from fastapi import status

from app.core.messages import (
    BAD_REQUEST,
    FORBIDDEN,
    INVALID_TOKEN,
    RESOURCE_CONFLICT,
    RESOURCE_NOT_FOUND,
)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.headers = headers


class NotFoundException(AppException):
    def __init__(self, message: str = RESOURCE_NOT_FOUND) -> None:
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    def __init__(self, message: str = RESOURCE_CONFLICT) -> None:
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class AuthenticationException(AppException):
    def __init__(self, message: str = INVALID_TOKEN) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = FORBIDDEN) -> None:
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class BadRequestException(AppException):
    def __init__(self, message: str = BAD_REQUEST) -> None:
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)
