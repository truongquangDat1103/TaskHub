from typing import Annotated

from fastapi import Path
from pydantic import PositiveInt

WorkspaceID = Annotated[PositiveInt, Path(description="Workspace ID", ge=1)]
ProjectID = Annotated[PositiveInt, Path(description="Project ID", ge=1)]
TaskID = Annotated[PositiveInt, Path(description="Task ID", ge=1)]
LabelID = Annotated[PositiveInt, Path(description="Label ID", ge=1)]
CommentID = Annotated[PositiveInt, Path(description="Comment ID", ge=1)]
UserID = Annotated[PositiveInt, Path(description="User ID", ge=1)]

__all__ = [
    "CommentID",
    "LabelID",
    "ProjectID",
    "TaskID",
    "UserID",
    "WorkspaceID",
]
