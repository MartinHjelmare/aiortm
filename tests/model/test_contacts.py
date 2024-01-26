"""Test the contacts model."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aioresponses import aioresponses
import pytest

from aiortm.client import AioRTMClient
from aiortm.exceptions import APIResponseError

from ..util import load_fixture


@pytest.fixture(name="contacts_add", scope="session")
def contacts_add_fixture() -> str:
    """Return a response for rtm.contacts.add."""
    return load_fixture("contacts/add.json")


@pytest.fixture(name="contacts_add_not_exist", scope="session")
def contacts_add_not_exist_fixture() -> str:
    """Return a response for rtm.contacts.add non existing contact."""
    return load_fixture("contacts/add_contact_not_exist.json")


@pytest.fixture(name="contacts_get_list", scope="session")
def contacts_get_list_fixture() -> str:
    """Return a response for rtm.contacts.getList."""
    return load_fixture("contacts/get_list.json")


@pytest.fixture(name="contacts_get_list_no_contacts", scope="session")
def contacts_get_list_no_contacts_fixture() -> str:
    """Return a response for rtm.contacts.getList with no contacts."""
    return load_fixture("contacts/get_list_no_contacts.json")


@pytest.fixture(name="contacts_delete", scope="session")
def contacts_delete_fixture() -> str:
    """Return a response for rtm.contacts.delete."""
    return load_fixture("contacts/delete.json")


@pytest.fixture(name="contacts_delete_invalid_contact_id", scope="session")
def contacts_delete_invalid_contact_id_fixture() -> str:
    """Return a response for rtm.contacts.delete for invalid contact id."""
    return load_fixture("contacts/delete_contact_id_invalid.json")


async def test_contacts_add(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_add: str,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts add."""
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
            method="rtm.contacts.add",
            timeline=1234567890,
            contact="john",
        ),
        body=contacts_add,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    contact_add_response = await client.rtm.contacts.add(
        timeline=timeline, contact="john"
    )

    assert contact_add_response.stat == "ok"
    assert contact_add_response.transaction.id == 12450053965
    assert contact_add_response.transaction.undoable == 0
    assert contact_add_response.contact.id == 1
    assert contact_add_response.contact.username == "john"
    assert contact_add_response.contact.fullname == "John Smith"


async def test_contacts_add_contact_not_exist(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_add_not_exist: str,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts add non existing contact."""
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
            method="rtm.contacts.add",
            timeline=1234567890,
            contact="missing-contact",
        ),
        body=contacts_add_not_exist,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    with pytest.raises(APIResponseError) as err:
        await client.rtm.contacts.add(timeline=timeline, contact="missing-contact")

    assert str(err.value) == "Contact requested does not exist."
    assert err.value.code == 1020


async def test_contacts_get_list(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_get_list: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts get list."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.contacts.getList",
        ),
        body=contacts_get_list,
    )

    result = await client.rtm.contacts.get_list()

    assert result.stat == "ok"
    assert result.contacts[0].id == 1
    assert result.contacts[0].fullname == "John Smith"
    assert result.contacts[0].username == "john"


async def test_contacts_get_list_no_contacts(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_get_list_no_contacts: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts get list with no contacts in the response."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.contacts.getList",
        ),
        body=contacts_get_list_no_contacts,
    )

    result = await client.rtm.contacts.get_list()

    assert result.stat == "ok"
    assert not result.contacts


async def test_contacts_delete(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_delete: str,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts delete."""
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
            method="rtm.contacts.delete",
            timeline=1234567890,
            contact_id=1234567,
        ),
        body=contacts_delete,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    contact_delete_response = await client.rtm.contacts.delete(
        timeline=timeline, contact_id=1234567
    )

    assert contact_delete_response.stat == "ok"
    assert contact_delete_response.transaction.id == 10638868055
    assert contact_delete_response.transaction.undoable == 0


async def test_contacts_delete_invalid_contact_id(
    client: AioRTMClient,
    mock_response: aioresponses,
    contacts_delete_invalid_contact_id: str,
    timelines_create: str,
    generate_url: Callable[..., str],
) -> None:
    """Test contacts delete."""
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
            method="rtm.contacts.delete",
            timeline=1234567890,
            contact_id=1234567,
        ),
        body=contacts_delete_invalid_contact_id,
    )

    timeline_response = await client.rtm.timelines.create()
    timeline = timeline_response.timeline
    with pytest.raises(APIResponseError) as err:
        await client.rtm.contacts.delete(timeline=timeline, contact_id=1234567)

    assert str(err.value) == "contact_id invalid or not provided"
    assert err.value.code == 360


@pytest.mark.parametrize(
    "method, method_params",
    [("add", {"contact": "john"}), ("delete", {"contact_id": 1234567})],
)
async def test_contacts_invalid_timeline(
    client: AioRTMClient,
    mock_response: aioresponses,
    timelines_create: str,
    timelines_invalid: str,
    generate_url: Callable[..., str],
    method: str,
    method_params: dict[str, Any],
) -> None:
    """Test contacts methods with invalid timeline."""
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
            method=f"rtm.contacts.{method}",
            timeline=0,
            **method_params,
        ),
        body=timelines_invalid,
    )

    with pytest.raises(APIResponseError) as err:
        method_object = getattr(client.rtm.contacts, method)
        await method_object(timeline=0, **method_params)

    assert str(err.value) == "Timeline invalid or not provided"
    assert err.value.code == 300
