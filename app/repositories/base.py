from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.db.base import Base
from app.schemas.pagination import PaginationParams

ModelT = TypeVar("ModelT", bound=Base)

PROTECTED_COLUMNS = frozenset({"id", "created_at"})


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, identifier: int) -> ModelT | None:
        return await self.session.get(self.model, identifier)

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def paginate(
        self,
        *filters: ColumnElement[bool],
        pagination: PaginationParams | None = None,
        order_by: Sequence[Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        page = pagination.page if pagination else DEFAULT_PAGE
        limit = pagination.limit if pagination else DEFAULT_PAGE_SIZE

        count_stmt = select(func.count()).select_from(self.model).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        order_clauses = list(order_by) if order_by is not None else []
        pk_col = getattr(self.model, "id", None)
        if pk_col is not None and pk_col not in order_clauses:
            order_clauses.append(pk_col)

        statement = (
            select(self.model)
            .where(*filters)
            .order_by(*order_clauses)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = list(await self.session.scalars(statement))
        return items, total

    async def list(
        self,
        *filters: ColumnElement[bool],
        page: int = DEFAULT_PAGE,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> list[ModelT]:
        items, _ = await self.paginate(
            *filters, pagination=PaginationParams(page=page, limit=limit)
        )
        return items

    async def count(self, *filters: ColumnElement[bool]) -> int:
        statement = select(func.count()).select_from(self.model).where(*filters)
        return (await self.session.execute(statement)).scalar_one()

    async def update(self, instance: ModelT, values: Mapping[str, object]) -> ModelT:
        allowed_columns = set(self.model.__mapper__.columns.keys()) - PROTECTED_COLUMNS
        for field, value in values.items():
            if field in allowed_columns:
                setattr(instance, field, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
