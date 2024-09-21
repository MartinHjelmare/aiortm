"""Provide a model for tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin

from .response import BaseResponse, TransactionResponse

if TYPE_CHECKING:
    from aiortm.client import Auth


@dataclass
class BaseModel(DataClassJSONMixin):
    """Represent a base model that turns empty string to None."""

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Turn empty string to None."""
        for k, v in d.items():
            if v == "":
                d[k] = None
            elif isinstance(v, list):
                d[k] = [cls.__pre_deserialize__(i) for i in v]
            elif isinstance(v, dict):
                d[k] = cls.__pre_deserialize__(v)
        return d


@dataclass
class TaskResponse(BaseModel):
    """Represent a response for a task."""

    id: int
    has_due_time: bool
    added: datetime = field(metadata={"deserialize": "ciso8601"})
    priority: Literal["N", "1", "2", "3"]
    postponed: bool
    due: datetime | None = field(metadata={"deserialize": "ciso8601"}, default=None)
    completed: datetime | None = field(
        metadata={"deserialize": "ciso8601"},
        default=None,
    )
    deleted: datetime | None = field(
        metadata={"deserialize": "ciso8601"},
        default=None,
    )
    estimate: str | None = None


@dataclass
class TaskSeriesResponse(BaseModel):
    """Represent a response for a task series."""

    id: int
    created: datetime = field(metadata={"deserialize": "ciso8601"})
    modified: datetime = field(metadata={"deserialize": "ciso8601"})
    name: str
    source: str
    tags: list[str]
    participants: list[str]
    notes: list[str]
    task: list[TaskResponse]
    location_id: str | None = None
    url: str | None = None


@dataclass
class TaskListResponse(BaseModel):
    """Represent a response for a task list."""

    id: int
    taskseries: list[TaskSeriesResponse]
    current: datetime | None = field(
        metadata={"deserialize": "ciso8601"},
        default=None,
    )


@dataclass
class RootTaskResponse(BaseModel):
    """Represent a response for the root tasks object."""

    rev: str
    task_list: list[TaskListResponse] = field(metadata=field_options(alias="list"))

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Ensure that taskseries exist."""
        task_list = d["list"]
        for item in task_list:
            if "taskseries" not in item:
                item["taskseries"] = []
        return d


@dataclass
class TaskModifiedResponse(BaseResponse):
    """Represent a response for a modified task."""

    transaction: TransactionResponse
    task_list: TaskListResponse = field(metadata=field_options(alias="list"))


@dataclass
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
            "rtm.tasks.add",
            timeline=timeline,
            name=name,
            list_id=list_id,
            parse="1" if parse else None,
        )
        return TaskModifiedResponse.from_dict(result)

    async def complete(
        self,
        timeline: int,
        list_id: int,
        taskseries_id: int,
        task_id: int,
    ) -> TaskModifiedResponse:
        """Complete a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.complete",
            timeline=timeline,
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )
        return TaskModifiedResponse.from_dict(result)

    async def delete(
        self,
        timeline: int,
        list_id: int,
        taskseries_id: int,
        task_id: int,
    ) -> TaskModifiedResponse:
        """Delete a task."""
        result = await self.api.call_api_auth(
            "rtm.tasks.delete",
            timeline=timeline,
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )
        return TaskModifiedResponse.from_dict(result)

    async def get_list(
        self,
        list_id: int | None = None,
        last_sync: datetime | None = None,
    ) -> TasksResponse:
        """Get a list of tasks."""
        last_sync_string: str | None = None
        if last_sync is not None:
            last_sync_string = last_sync.isoformat()

        result = await self.api.call_api_auth(
            "rtm.tasks.getList",
            list_id=list_id,
            last_sync=last_sync_string,
        )
        return TasksResponse.from_dict(result)

    async def set_name(
        self,
        timeline: int,
        list_id: int,
        taskseries_id: int,
        task_id: int,
        name: str,
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
        return TaskModifiedResponse.from_dict(result)
