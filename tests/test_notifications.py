from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.dependencies import get_email_service
from app.core.security import create_access_token
from app.main import app
from app.models.enums import TaskPriority
from app.services.email import EmailService
from tests.conftest import TEST_JWT_SECRET


def auth_headers(user_id: int = 1) -> dict[str, str]:
    token = create_access_token(subject=user_id, secret_key=TEST_JWT_SECRET)
    return {"Authorization": f"Bearer {token}"}


def test_background_task_sends_email_on_task_create(database_url: str) -> None:
    fake_email_service = EmailService()
    fake_email_service.send_task_assigned_email = MagicMock(
        wraps=fake_email_service.send_task_assigned_email
    )
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        with TestClient(app, headers=auth_headers(1)) as client:
            res = client.post(
                "/api/v1/projects/1/tasks",
                json={
                    "title": "Email Notification Task",
                    "priority": TaskPriority.HIGH.value,
                    "assignee_id": 1,
                },
            )
            assert res.status_code == 201
            # Check background task was executed
            assert fake_email_service.send_task_assigned_email.call_count == 1
            call_kwargs = fake_email_service.send_task_assigned_email.call_args.kwargs
            assert call_kwargs["to_email"] == "owner@example.com"
            assert call_kwargs["task_title"] == "Email Notification Task"
            assert len(fake_email_service.sent_emails) == 1
    finally:
        app.dependency_overrides.pop(get_email_service, None)


def test_background_task_sends_email_on_assignee_change(database_url: str) -> None:
    fake_email_service = EmailService()
    fake_email_service.send_task_assigned_email = MagicMock(
        wraps=fake_email_service.send_task_assigned_email
    )
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    try:
        with TestClient(app, headers=auth_headers(1)) as client:
            # 1. Create task without assignee -> no email
            res = client.post(
                "/api/v1/projects/1/tasks",
                json={"title": "Unassigned Task"},
            )
            assert res.status_code == 201
            task_id = res.json()["id"]
            assert fake_email_service.send_task_assigned_email.call_count == 0

            # 2. Update task with assignee -> email dispatched
            update_res = client.patch(
                f"/api/v1/tasks/{task_id}",
                json={"assignee_id": 1},
            )
            assert update_res.status_code == 200
            assert fake_email_service.send_task_assigned_email.call_count == 1
            assert len(fake_email_service.sent_emails) == 1
            assert (
                fake_email_service.sent_emails[0]["subject"]
                == "You have been assigned to task: Unassigned Task"
            )
    finally:
        app.dependency_overrides.pop(get_email_service, None)
