"""Test the tasks model."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from aioresponses import aioresponses
import pytest

from aiortm.client import AioRTMClient
from tests.util import load_fixture


@pytest.fixture(name="tasks_add", scope="module")
def tasks_add_fixture() -> str:
    """Return a response for rtm.tasks.add."""
    return load_fixture("tasks/add.json")


@pytest.fixture(name="tasks_set_name", scope="module")
def tasks_set_name_fixture() -> str:
    """Return a response for rtm.tasks.setName."""
    return load_fixture("tasks/set_name.json")


@pytest.fixture(name="response")
def response_fixture(request: pytest.FixtureRequest) -> str:
    """Return a response for the rtm api."""
    return load_fixture(request.param)


async def test_tasks_add(
    client: AioRTMClient,
    mock_response: aioresponses,
    tasks_add: str,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test tasks add."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.timelines.create",
        ),
        body=timelines_create,
    )
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.tasks.add",
            timeline=1234567890,
            name="Test task",
        ),
        body=tasks_add,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    result = await client.rtm.tasks.add(timeline=timeline, name="Test task")

    assert result.stat == "ok"
    assert result.transaction.id == 12451745176
    assert result.transaction.undoable == 0
    assert result.task_list.id == 48730705
    assert result.task_list.taskseries[0].id == 493137362
    assert result.task_list.taskseries[0].created == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )
    assert result.task_list.taskseries[0].modified == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )
    assert result.task_list.taskseries[0].name == "Test task"
    assert result.task_list.taskseries[0].source == "api:test-api-key"
    assert result.task_list.taskseries[0].task[0].id == 924832826
    assert result.task_list.taskseries[0].task[0].added == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )


@pytest.mark.parametrize(
    ("method", "transaction", "modified", "deleted", "response"),
    [
        (
            "complete",
            12475899884,
            datetime.fromisoformat("2023-01-05T00:04:52+00:00"),
            None,
            "tasks/complete.json",
        ),
        (
            "delete",
            12476056249,
            datetime.fromisoformat("2023-01-05T00:34:45+00:00"),
            datetime.fromisoformat("2023-01-05T00:34:45+00:00"),
            "tasks/delete.json",
        ),
    ],
    indirect=["response"],
)
async def test_tasks_complete_delete(
    client: AioRTMClient,
    mock_response: aioresponses,
    timelines_create: str,
    generate_url: Callable[..., str],
    method: str,
    transaction: int,
    modified: datetime,
    deleted: datetime | None,
    response: str,
) -> None:
    """Test tasks complete and delete."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.timelines.create",
        ),
        body=timelines_create,
    )
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method=f"rtm.tasks.{method}",
            timeline=1234567890,
            list_id=48730705,
            taskseries_id=493137362,
            task_id=924832826,
        ),
        body=response,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    method_object = getattr(client.rtm.tasks, method)
    result = await method_object(
        timeline=timeline,
        list_id=48730705,
        taskseries_id=493137362,
        task_id=924832826,
    )

    assert result.stat == "ok"
    assert result.transaction.id == transaction
    assert result.transaction.undoable == 1
    assert result.task_list.id == 48730705
    assert result.task_list.taskseries[0].id == 493137362
    assert result.task_list.taskseries[0].created == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )
    assert result.task_list.taskseries[0].modified == modified
    assert result.task_list.taskseries[0].name == "Test task"
    assert result.task_list.taskseries[0].source == "api:test-api-key"
    assert result.task_list.taskseries[0].task[0].id == 924832826
    assert result.task_list.taskseries[0].task[0].completed == datetime.fromisoformat(
        "2023-01-05T00:04:52+00:00",
    )
    assert result.task_list.taskseries[0].task[0].deleted == deleted


@pytest.mark.parametrize(
    ("response", "response_params", "method_params", "current"),
    [
        (
            "tasks/get_list.json",
            {},
            {},
            None,
        ),
        (
            "tasks/get_list_last_sync.json",
            {"last_sync": "2022-05-18T14:27:08+00:00"},
            {"last_sync": datetime.fromisoformat("2022-05-18T14:27:08+00:00")},
            datetime.fromisoformat("2022-05-18T14:27:08+00:00"),
        ),
    ],
    indirect=["response"],
)
async def test_tasks_get_list(
    client: AioRTMClient,
    mock_response: aioresponses,
    generate_url: Callable[..., str],
    response: str,
    response_params: dict[str, Any],
    method_params: dict[str, Any],
    current: datetime | None,
) -> None:
    """Test tasks get list."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.tasks.getList",
            **response_params,
        ),
        body=response,
    )

    result = await client.rtm.tasks.get_list(**method_params)

    assert result.stat == "ok"
    assert result.tasks.rev
    assert result.tasks.task_list[0].id == 48730705
    assert result.tasks.task_list[0].current == current
    assert result.tasks.task_list[0].taskseries[0].id == 493137362
    assert result.tasks.task_list[0].taskseries[0].created == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )
    assert result.tasks.task_list[0].taskseries[0].modified == datetime.fromisoformat(
        "2023-01-02T01:55:25+00:00",
    )
    assert result.tasks.task_list[0].taskseries[0].name == "Test task"
    assert result.tasks.task_list[0].taskseries[0].source == "api:test-api-key"
    assert result.tasks.task_list[0].taskseries[0].task[0].id == 924832826
    assert result.tasks.task_list[0].taskseries[0].task[
        0
    ].added == datetime.fromisoformat("2023-01-02T01:55:25+00:00")


async def test_tasks_set_name(
    client: AioRTMClient,
    mock_response: aioresponses,
    timelines_create: str,
    generate_url: Callable[..., str],
    tasks_set_name: str,
) -> None:
    """Test tasks set name."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.timelines.create",
        ),
        body=timelines_create,
    )
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.tasks.setName",
            timeline=1234567890,
            list_id=48730705,
            taskseries_id=493427774,
            task_id=925539907,
            name="Renamed task",
        ),
        body=tasks_set_name,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    result = await client.rtm.tasks.set_name(
        timeline=timeline,
        list_id=48730705,
        taskseries_id=493427774,
        task_id=925539907,
        name="Renamed task",
    )

    assert result.stat == "ok"
    assert result.transaction.id == 12476388930
    assert result.transaction.undoable == 1
    assert result.task_list.id == 48730705
    assert result.task_list.taskseries[0].id == 493427774
    assert result.task_list.taskseries[0].created == datetime.fromisoformat(
        "2023-01-05T01:39:14+00:00",
    )
    assert result.task_list.taskseries[0].modified == datetime.fromisoformat(
        "2023-01-05T01:42:01+00:00",
    )
    assert result.task_list.taskseries[0].name == "Renamed task"
    assert result.task_list.taskseries[0].source == "api:test-api-key"
    assert result.task_list.taskseries[0].task[0].id == 925539907
    assert result.task_list.taskseries[0].task[0].added == datetime.fromisoformat(
        "2023-01-05T01:39:14+00:00",
    )
