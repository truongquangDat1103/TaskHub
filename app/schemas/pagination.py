from typing import Generic, TypeVar

from pydantic import Field, PositiveInt

from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.schemas.base import BaseSchema

T = TypeVar("T")


class PaginationParams(BaseSchema):
    page: int = Field(default=DEFAULT_PAGE, ge=DEFAULT_PAGE)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=DEFAULT_PAGE, le=MAX_PAGE_SIZE)


class Page(BaseSchema, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: PositiveInt
    limit: PositiveInt
