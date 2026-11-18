import pytest
from pydantic import ValidationError

from app.core.constants import TASK_TITLE_MAX_LENGTH
from app.core.exceptions import NotFoundException
from app.schemas.task import TaskCreate, TaskUpdate


def test_task_create_schema_strips_whitespace() -> None:
    task = TaskCreate(title="   Clean Code   ", project_id=1)
    assert task.title == "Clean Code"


def test_task_create_schema_rejects_blank_or_too_long() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(title="   ", project_id=1)
    with pytest.raises(ValidationError):
        TaskCreate(title="a" * (TASK_TITLE_MAX_LENGTH + 1), project_id=1)


def test_task_update_schema_rejects_explicit_null() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate.model_validate({"title": None})


def test_task_update_schema_allows_nullable_description() -> None:
    update = TaskUpdate.model_validate({"description": None})
    assert update.description is None


def test_custom_not_found_exception() -> None:
    exc = NotFoundException("Task not found")
    assert exc.status_code == 404
    assert exc.message == "Task not found"
