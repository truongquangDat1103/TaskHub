from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("taskhub.email")


class EmailService:
    def __init__(self) -> None:
        self.sent_emails: list[dict[str, Any]] = []

    def send_task_assigned_email(
        self,
        *,
        to_email: str,
        task_id: int,
        task_title: str,
        project_id: int,
        assigner_name: str,
    ) -> None:
        """Simulate sending an email notification asynchronously via BackgroundTasks."""
        message = {
            "to": to_email,
            "subject": f"You have been assigned to task: {task_title}",
            "task_id": task_id,
            "task_title": task_title,
            "project_id": project_id,
            "assigner": assigner_name,
        }
        self.sent_emails.append(message)
        logger.info(
            "Background Task: Notification email dispatched to %s for task #%d '%s' by %s",
            to_email,
            task_id,
            task_title,
            assigner_name,
        )


email_service = EmailService()


def get_email_service() -> EmailService:
    return email_service
