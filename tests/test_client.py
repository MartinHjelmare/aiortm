"""Test the client module."""

from __future__ import annotations

from collections.abc import Callable

from aioresponses import aioresponses
import pytest

from aiortm.client import AioRTMClient

from .util import load_fixture


@pytest.fixture(name="get_frob", scope="module")
def get_frob_fixture() -> str:
    """Return a response for rtm.auth.getFrob."""
    return load_fixture("auth/get_frob.json")


@pytest.fixture(name="get_token", scope="module")
def get_token_fixture() -> str:
    """Return a response for rtm.auth.getToken."""
    return load_fixture("auth/get_token.json")


@pytest.fixture(name="check_token", scope="module")
def check_token_fixture() -> str:
    """Return a response for rtm.auth.checkToken."""
    return load_fixture("auth/check_token.json")


async def test_authenticate_desktop(
    client: AioRTMClient,
    mock_response: aioresponses,
    get_frob: str,
    generate_url: Callable[..., str],
) -> None:
    """Test the authenticate desktop method."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            method="rtm.auth.getFrob",
        ),
        body=get_frob,
    )

    url, frob = await client.rtm.api.authenticate_desktop()

    assert url == (
        "https://www.rememberthemilk.com/services/auth/?"
        "api_key=test-api-key&perms=delete&frob=test-frob"
        "&api_sig=9d28d5a58ff2efc3fed277a58c3ce818"
    )
    assert frob == "test-frob"


async def test_get_token(
    client: AioRTMClient,
    mock_response: aioresponses,
    get_token: str,
    generate_url: Callable[..., str],
) -> None:
    """Test the get_token method."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            frob="test-frob",
            method="rtm.auth.getToken",
        ),
        body=get_token,
    )

    result = await client.rtm.api.get_token("test-frob")

    assert result["token"] == "test-token"
    assert result["perms"] == "delete"
    assert result["user"]["id"] == "1234567"
    assert result["user"]["username"] == "johnsmith"
    assert result["user"]["fullname"] == "John Smith"


async def test_check_token(
    client: AioRTMClient,
    mock_response: aioresponses,
    check_token: str,
    generate_url: Callable[..., str],
) -> None:
    """Test the check_token method."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.auth.checkToken",
        ),
        body=check_token,
    )

    result = await client.rtm.api.check_token()

    assert result["token"] == "test-token"
    assert result["perms"] == "delete"
    assert result["user"]["id"] == "1234567"
    assert result["user"]["username"] == "johnsmith"
    assert result["user"]["fullname"] == "John Smith"
