import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.session import create_database_engine
from app.models import Project
from app.repositories.base import BaseRepository
from app.schemas.pagination import PaginationParams


def test_repository_crud_persists_between_sessions(database_url: str) -> None:
    async def check_crud() -> None:
        engine = create_database_engine(database_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory.begin() as session:
                repository = BaseRepository(Project, session)
                project = await repository.create(Project(workspace_id=1, name="New"))
                project_id = project.id
                assert project.created_at is not None
            async with factory.begin() as session:
                repository = BaseRepository(Project, session)
                project = await repository.get(project_id)
                assert project.name == "New"
                await repository.update(
                    project,
                    {"name": "Updated", "id": 9999, "non_existent_key": "val"},
                )
                assert project.id == project_id
                assert not hasattr(project, "non_existent_key")
            async with factory.begin() as session:
                repository = BaseRepository(Project, session)
                project = await repository.get(project_id)
                assert project.name == "Updated"
                await repository.delete(project)
            async with factory() as session:
                assert await BaseRepository(Project, session).get(project_id) is None
        finally:
            await engine.dispose()

    asyncio.run(check_crud())


def test_repository_pagination_and_count(database_url: str) -> None:
    async def check_pages() -> None:
        engine = create_database_engine(database_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory.begin() as session:
                repository = BaseRepository(Project, session)
                for name in ("First", "Second", "Third"):
                    await repository.create(Project(workspace_id=1, name=name))
            async with factory() as session:
                repository = BaseRepository(Project, session)
                projects = await repository.list(page=2, limit=2)
                assert [project.name for project in projects] == ["Second", "Third"]
                items, total = await repository.paginate(
                    pagination=PaginationParams(page=2, limit=2)
                )
                assert [p.name for p in items] == ["Second", "Third"]
                assert total == 4
                assert await repository.count() == 4
                assert await repository.list(page=4, limit=2) == []
        finally:
            await engine.dispose()

    asyncio.run(check_pages())


def test_repository_does_not_commit_the_callers_transaction(database_url: str) -> None:
    async def check_rollback() -> None:
        engine = create_database_engine(database_url)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with factory() as session:
                project = await BaseRepository(Project, session).create(
                    Project(workspace_id=1, name="Will roll back")
                )
                project_id = project.id
                await session.rollback()
            async with factory() as session:
                assert await BaseRepository(Project, session).get(project_id) is None
        finally:
            await engine.dispose()

    asyncio.run(check_rollback())
