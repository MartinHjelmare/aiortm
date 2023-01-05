"""Provide a model for tasks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import BaseModel as PydanticBaseModel, Field, validator

from .response import BaseResponse, TransactionResponse

if TYPE_CHECKING:
    from ..client import Auth

# pylint: disable=consider-alternative-union-syntax


class BaseModel(PydanticBaseModel):
    """Represent a base model that turns empty string to None."""

    @validator("*", pre=True)
    def empty_str_to_none(cls, value: Any) -> Any:  # pylint: disable=no-self-argument
        """Turn empty string to None."""
        if value == "":
            return None
        return value


class TaskResponse(BaseModel):
    """Represent a response for a task."""

    id: int
    due: Optional[datetime]
    has_due_time: bool
    added: datetime
    completed: Optional[datetime]
    deleted: Optional[datetime]
    priority: Literal["N", "1", "2", "3"]
    postponed: bool
    estimate: Optional[str]


class TaskSeriesResponse(BaseModel):
    """Represent a response for a task series."""

    id: int
    created: datetime
    modified: datetime
    name: str
    source: str
    location_id: Optional[str]
    url: Optional[str]
    tags: list[str]
    participants: list[str]
    notes: list[str]
    task: list[TaskResponse]


class TaskListResponse(BaseModel):
    """Represent a response for a task list."""

    id: int
    taskseries: list[TaskSeriesResponse]
    current: Optional[datetime]


class RootTaskResponse(BaseModel):
    """Represent a response for the root tasks object."""

    rev: str
    task_list: list[TaskListResponse] = Field(..., alias="list")

    @validator("task_list", pre=True)
    def ensure_taskseries(  # pylint: disable=no-self-argument
        cls, value: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Ensure that taskseries exist."""
        for item in value:
            if "taskseries" not in item:
                item["taskseries"] = []
        return value


class TaskModifiedResponse(BaseResponse):
    """Represent a response for a modified task."""

    transaction: TransactionResponse
    task_list: TaskListResponse = Field(..., alias="list")


class TasksResponse(BaseResponse):
    """Represent a response for a list of tasks."""

    tasks: RootTaskResponse


@dataclass
class Tasks:
    """Represent the tasks model."""

    api: Auth

    async def add(
        self,
        timeline: int,
        name: str,
        list_id: int | None = None,
        parse: bool | None = None,
    ) -> TaskModifiedResponse:
        """Add a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.add", timeline=timeline, name=name, list_id=list_id, parse=parse
        )
        return TaskModifiedResponse(**result)

    async def complete(
        self, timeline: int, list_id: int, taskseries_id: int, task_id: int
    ) -> TaskModifiedResponse:
        """Complete a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.complete",
            timeline=timeline,
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )
        return TaskModifiedResponse(**result)

    async def delete(
        self, timeline: int, list_id: int, taskseries_id: int, task_id: int
    ) -> TaskModifiedResponse:
        """Delete a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.delete",
            timeline=timeline,
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )
        return TaskModifiedResponse(**result)

    async def get_list(
        self, list_id: int | None = None, last_sync: datetime | None = None
    ) -> TasksResponse:
        """Get a list of tasks."""
        last_sync_string: str | None = None
        if last_sync is not None:
            last_sync_string = last_sync.isoformat()

        result = await self.api.call_api_auth(
            "rtm.tasks.getList", list_id=list_id, last_sync=last_sync_string
        )
        return TasksResponse(**result)

    async def set_name(
        self, timeline: int, list_id: int, taskseries_id: int, task_id: int, name: str
    ) -> TaskModifiedResponse:
        """Rename a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.setName",
            timeline=timeline,
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            name=name,
        )
        return TaskModifiedResponse(**result)
