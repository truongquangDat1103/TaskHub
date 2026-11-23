from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    PositiveInt,
    field_serializer,
    field_validator,
)

from app.core.constants import (
    TASK_DESCRIPTION_MAX_LENGTH,
    TASK_TITLE_MAX_LENGTH,
    TASK_TITLE_MIN_LENGTH,
)
from app.core.messages import DUE_DATE_PAST, FIELD_CANNOT_BE_NULL
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import BaseSchema
from app.schemas.pagination import Page, PaginationParams

TaskTitle = Annotated[
    str, Field(min_length=TASK_TITLE_MIN_LENGTH, max_length=TASK_TITLE_MAX_LENGTH)
]
TaskDescription = Annotated[str, Field(max_length=TASK_DESCRIPTION_MAX_LENGTH)]


def _validate_utc_datetime(value: datetime | None) -> datetime | None:
    if value is not None:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return value


def _validate_future_utc_datetime(value: datetime | None) -> datetime | None:
    value = _validate_utc_datetime(value)
    if value is not None and value <= datetime.now(UTC):
        raise ValueError(DUE_DATE_PAST)
    return value


UtcDatetime = Annotated[datetime, AfterValidator(_validate_utc_datetime)]
FutureUtcDatetime = Annotated[datetime, AfterValidator(_validate_future_utc_datetime)]


class TaskBase(BaseSchema):
    title: TaskTitle
    description: TaskDescription | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: PositiveInt | None = None
    due_date: FutureUtcDatetime | None = Field(
        default=None, description="Due date in UTC"
    )


class TaskCreate(TaskBase):
    project_id: PositiveInt


class ProjectTaskCreate(TaskBase):
    pass


class TaskUpdate(BaseSchema):
    title: TaskTitle | None = None
    description: TaskDescription | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: PositiveInt | None = None
    due_date: FutureUtcDatetime | None = Field(
        default=None, description="Due date in UTC"
    )

    @field_validator("title", "status", "priority")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError(FIELD_CANNOT_BE_NULL)
        return value


class TaskRead(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt
    title: str
    description: str | None = None
    status: TaskStatus
    priority: TaskPriority
    project_id: PositiveInt
    assignee_id: PositiveInt | None = None
    due_date: datetime | None = None
    created_by: PositiveInt
    created_at: datetime

    @field_serializer("due_date", "created_at", when_used="json")
    def serialize_datetime(self, v: datetime | None) -> str | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
        return v.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ProjectTaskQuery(PaginationParams):
    q: TaskTitle | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: PositiveInt | None = None


class TaskQuery(ProjectTaskQuery):
    project_id: PositiveInt | None = None


TaskPage = Page[TaskRead]
