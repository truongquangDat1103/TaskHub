from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def enum_column(enum_cls: type[PyEnum], name: str, default: Any = None) -> Any:
    server_default = (
        default.value
        if hasattr(default, "value")
        else (str(default) if default is not None else None)
    )
    return mapped_column(
        SAEnum(enum_cls, native_enum=False, create_constraint=True, name=name),
        default=default,
        server_default=server_default,
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
