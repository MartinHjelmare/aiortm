"""Provide common pytest fixtures."""

from collections.abc import AsyncGenerator, Callable, Generator
import logging
from typing import Any

from aiohttp import ClientSession
from aioresponses import aioresponses
import pytest
from yarl import URL

from aiortm.client import REST_URL, AioRTMClient, Auth

from .util import load_fixture


@pytest.fixture(autouse=True)
def debug_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Set logging level to debug."""
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def mock_response() -> Generator[aioresponses, None, None]:
    """Provide a mocker for aiohttp responses."""
    with aioresponses() as mock_response_:
        yield mock_response_


@pytest.fixture(name="session")
async def session_fixture() -> AsyncGenerator[ClientSession, None]:
    """Provide a aiohttp client session."""
    async with ClientSession() as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: ClientSession) -> AioRTMClient:
    """Provide a test client."""
    return AioRTMClient(
        Auth(
            client_session=session,
            api_key="test-api-key",
            shared_secret="test-shared-secret",
            auth_token="test-token",
            permission="delete",
        )
    )


@pytest.fixture
def generate_url(client: AioRTMClient) -> Callable[..., str]:
    """Generate a URL from params."""

    def generate_url_(**params: Any) -> str:
        all_params = params | {"format": "json"}
        # pylint: disable-next=protected-access
        all_params |= {"api_sig": client.rtm.api._sign_request(all_params)}
        return str(URL(REST_URL).with_query(all_params))

    return generate_url_


@pytest.fixture(scope="session")
def timelines_create() -> str:
    """Return a response for rtm.timelines.create."""
    return load_fixture("timelines/create.json")


@pytest.fixture(scope="session")
def timelines_invalid() -> str:
    """Return a response for invalid timeline."""
    return load_fixture("timelines/invalid.json")
