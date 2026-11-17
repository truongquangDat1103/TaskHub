from __future__ import annotations

from fastapi import BackgroundTasks

from app.core.constants import (
    ASSIGNEE_NOT_FOUND,
    ASSIGNEE_NOT_WORKSPACE_MEMBER,
    CREATOR_NOT_FOUND,
    PROJECT_FORBIDDEN,
    PROJECT_NOT_FOUND,
    TASK_FORBIDDEN,
    TASK_NOT_FOUND,
)
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.models import Project, Task, User
from app.models.enums import UserRole
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.task import (
    ProjectTaskQuery,
    TaskCreate,
    TaskPage,
    TaskQuery,
    TaskRead,
    TaskUpdate,
)
from app.services.cache import TaskCacheService
from app.services.email import EmailService
from app.services.permissions import require_project_access


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        workspace_repository: WorkspaceRepository,
        cache_service: TaskCacheService | None = None,
        email_service: EmailService | None = None,
    ) -> None:
        self.repository = repository
        self.workspace_repository = workspace_repository
        self.cache_service = cache_service or TaskCacheService()
        self.email_service = email_service or EmailService()

    async def _require_project(self, project_id: int) -> Project:
        project = await self.repository.get_project(project_id)
        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)
        return project

    async def _check_project_access(
        self,
        project: Project,
        user: User,
        *,
        write: bool = False,
        forbidden_message: str = PROJECT_FORBIDDEN,
    ) -> None:
        await require_project_access(
            self.workspace_repository,
            project,
            user,
            write=write,
            forbidden_message=forbidden_message,
        )

    async def get(self, task_id: int, user: User) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)
        if user.role != UserRole.ADMIN:
            project = await self._require_project(task.project_id)
            await self._check_project_access(
                project, user, write=False, forbidden_message=TASK_FORBIDDEN
            )
        return task

    async def create(
        self,
        payload: TaskCreate,
        user: User,
        background_tasks: BackgroundTasks | None = None,
    ) -> Task:
        project = await self._require_project(payload.project_id)
        await self._check_project_access(project, user, write=True)
        if not await self.repository.user_exists(user.id):
            raise NotFoundException(CREATOR_NOT_FOUND)
        assignee = await self.check_assignee(payload.assignee_id, project.workspace_id)
        task = await self.repository.create(
            Task(**payload.model_dump(), created_by=user.id)
        )
        await self.cache_service.invalidate_project_tasks(payload.project_id)
        if background_tasks is not None and assignee is not None and assignee.email:
            background_tasks.add_task(
                self.email_service.send_task_assigned_email,
                to_email=assignee.email,
                task_id=task.id,
                task_title=task.title,
                project_id=task.project_id,
                assigner_name=user.full_name,
            )
        return task

    async def list(self, query: TaskQuery, user: User) -> TaskPage:
        is_admin = user.role == UserRole.ADMIN
        tasks, total = await self.repository.search(
            user_id=user.id,
            is_admin=is_admin,
            **query.model_dump(),
        )
        return TaskPage(
            items=[TaskRead.model_validate(task) for task in tasks],
            total=total,
            page=query.page,
            limit=query.limit,
        )

    async def list_by_project(
        self, project_id: int, query: ProjectTaskQuery, user: User
    ) -> TaskPage:
        project = await self._require_project(project_id)
        await self._check_project_access(project, user, write=False)
        cached = await self.cache_service.get_project_tasks(project_id, query)
        if cached is not None:
            return cached
        task_query = TaskQuery(**query.model_dump(), project_id=project_id)
        page = await self.list(task_query, user)
        await self.cache_service.set_project_tasks(project_id, query, page)
        return page

    async def update(
        self,
        task_id: int,
        payload: TaskUpdate,
        user: User,
        background_tasks: BackgroundTasks | None = None,
    ) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)
        project = await self._require_project(task.project_id)
        await self._check_project_access(
            project, user, write=True, forbidden_message=TASK_FORBIDDEN
        )
        values = payload.model_dump(exclude_unset=True)
        old_assignee_id = task.assignee_id
        new_assignee: User | None = None
        if "assignee_id" in values:
            new_assignee = await self.check_assignee(
                payload.assignee_id, project.workspace_id
            )
        if not values:
            return task
        updated = await self.repository.update(task, values)
        await self.cache_service.invalidate_project_tasks(task.project_id)
        if (
            background_tasks is not None
            and "assignee_id" in values
            and values["assignee_id"] is not None
            and values["assignee_id"] != old_assignee_id
            and new_assignee is not None
            and new_assignee.email
        ):
            background_tasks.add_task(
                self.email_service.send_task_assigned_email,
                to_email=new_assignee.email,
                task_id=updated.id,
                task_title=updated.title,
                project_id=updated.project_id,
                assigner_name=user.full_name,
            )
        return updated

    async def delete(self, task_id: int, user: User) -> None:
        task = await self.repository.get(task_id)
        if task is None:
            raise NotFoundException(TASK_NOT_FOUND)
        project = await self._require_project(task.project_id)
        await self._check_project_access(
            project, user, write=True, forbidden_message=TASK_FORBIDDEN
        )
        project_id = task.project_id
        await self.repository.delete(task)
        await self.cache_service.invalidate_project_tasks(project_id)

    async def check_assignee(
        self, assignee_id: int | None, workspace_id: int
    ) -> User | None:
        if assignee_id is None:
            return None
        assignee = await self.repository.session.get(User, assignee_id)
        if assignee is None:
            raise NotFoundException(ASSIGNEE_NOT_FOUND)
        role = await self.workspace_repository.get_effective_role(
            workspace_id, assignee_id
        )
        if role is None:
            raise BadRequestException(ASSIGNEE_NOT_WORKSPACE_MEMBER)
        return assignee
