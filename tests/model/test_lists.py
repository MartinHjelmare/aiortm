"""Test the lists model."""

from __future__ import annotations

from collections.abc import Callable

from aiointercept import aiointercept

from aiortm.client import AioRTMClient
from tests.util import load_fixture


async def test_lists_get_list(
    client: AioRTMClient,
    mock_response: aiointercept,
    generate_url: Callable[..., str],
) -> None:
    """Test lists get list."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.lists.getList",
        ),
        body=load_fixture("lists/get_list.json"),
    )

    result = await client.rtm.lists.get_list()

    assert result.stat == "ok"
    assert len(result.lists) == 2

    inbox = result.lists[0]
    assert inbox.id == 1
    assert inbox.name == "Inbox"
    assert inbox.deleted is False
    assert inbox.locked is True
    assert inbox.archived is False
    assert inbox.position == -1
    assert inbox.smart is False
    assert inbox.list_filter is None
    assert inbox.sort_order is None

    high_priority = result.lists[1]
    assert high_priority.id == 2
    assert high_priority.name == "High Priority"
    assert high_priority.deleted is False
    assert high_priority.locked is False
    assert high_priority.archived is False
    assert high_priority.position == 0
    assert high_priority.smart is True
    assert high_priority.list_filter == "(priority:1)"
    assert high_priority.sort_order == 0


async def test_lists_add(
    client: AioRTMClient,
    mock_response: aiointercept,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test lists add."""
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
            method="rtm.lists.add",
            timeline=1234567890,
            name="New List",
        ),
        body=load_fixture("lists/add.json"),
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    result = await client.rtm.lists.add(timeline=timeline, name="New List")

    assert result.stat == "ok"
    assert result.transaction.id == 987654321
    assert result.transaction.undoable == 1
    assert result.list.id == 123456789
    assert result.list.name == "New List"
    assert result.list.deleted is False
    assert result.list.locked is False
    assert result.list.archived is False
    assert result.list.position == 0
    assert result.list.smart is False
    assert result.list.list_filter is None
    assert result.list.sort_order == 0


async def test_lists_set_name(
    client: AioRTMClient,
    mock_response: aiointercept,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test lists set name."""
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
            method="rtm.lists.setName",
            timeline=1234567890,
            list_id=123456789,
            name="Renamed List",
        ),
        body=load_fixture("lists/set_name.json"),
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    result = await client.rtm.lists.set_name(
        timeline=timeline,
        list_id=123456789,
        name="Renamed List",
    )

    assert result.stat == "ok"
    assert result.transaction.id == 987654321
    assert result.transaction.undoable == 1
    assert result.list.id == 123456789
    assert result.list.name == "Renamed List"
    assert result.list.deleted is False
    assert result.list.locked is False
    assert result.list.archived is False
    assert result.list.position == 0
    assert result.list.smart is False
    assert result.list.list_filter is None
    assert result.list.sort_order == 0
