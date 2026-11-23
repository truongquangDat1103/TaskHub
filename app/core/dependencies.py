from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]

__all__ = [
    "SessionDep",
    "Settings",
    "get_db_session",
    "get_session",
    "get_settings",
]

get_db_session = get_session
