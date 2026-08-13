"""Test the client module."""

from __future__ import annotations

from collections.abc import Callable

from aiointercept import aiointercept
import pytest

from aiortm.client import AioRTMClient
from aiortm.exceptions import (
    APIAuthError,
    TransportAuthError,
    TransportError,
    TransportResponseError,
)

from .util import load_fixture


@pytest.fixture(name="not_logged_in", scope="module")
def not_logged_in_fixture() -> str:
    """Return a fail response with error code 99."""
    return load_fixture("auth/not_logged_in_bad_permission.json")


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
    mock_response: aiointercept,
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
    mock_response: aiointercept,
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


async def test_call_api_transport_response_error(
    client: AioRTMClient,
    mock_response: aiointercept,
    generate_url: Callable[..., str],
) -> None:
    """Test that TransportResponseError is raised for HTTP error responses."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.auth.checkToken",
        ),
        status=500,
    )

    with pytest.raises(TransportResponseError) as err:
        await client.rtm.api.check_token()

    assert err.value.client_error.status == 500


@pytest.mark.parametrize("status", [401, 403])
async def test_call_api_transport_auth_error(
    client: AioRTMClient,
    mock_response: aiointercept,
    generate_url: Callable[..., str],
    status: int,
) -> None:
    """Test that TransportAuthError is raised for 401/403 HTTP responses."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.auth.checkToken",
        ),
        status=status,
    )

    with pytest.raises(TransportAuthError):
        await client.rtm.api.check_token()


async def test_call_api_auth_error(
    client: AioRTMClient,
    mock_response: aiointercept,
    not_logged_in: str,
    generate_url: Callable[..., str],
) -> None:
    """Test that APIAuthError is raised for API auth error responses."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.auth.checkToken",
        ),
        body=not_logged_in,
    )

    with pytest.raises(APIAuthError) as err:
        await client.rtm.api.check_token()

    assert err.value.code == 99


async def test_call_api_transport_connection_error(
    client: AioRTMClient,
    mock_response: aiointercept,
    generate_url: Callable[..., str],
) -> None:
    """Test that TransportError is raised for connection errors."""
    mock_response.get(
        generate_url(
            api_key="test-api-key",
            auth_token="test-token",
            method="rtm.auth.checkToken",
        ),
        exception=True,
    )

    with pytest.raises(TransportError):
        await client.rtm.api.check_token()


async def test_check_token(
    client: AioRTMClient,
    mock_response: aiointercept,
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
