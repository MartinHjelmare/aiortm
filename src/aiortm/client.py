"""Provide a client for aiortm."""

from __future__ import annotations

import hashlib
from http import HTTPStatus
import json
import logging
from typing import Any, cast

from aiohttp import ClientResponse, ClientResponseError, ClientSession
from yarl import URL

from .exceptions import (
    APIAuthError,
    APIResponseError,
    TransportAuthError,
    TransportResponseError,
)
from .model import RTM
from .model.response import BaseErrorResponse

AUTH_URL = "https://www.rememberthemilk.com/services/auth/"
REST_URL = "https://api.rememberthemilk.com/services/rest/"
_LOGGER = logging.getLogger(__package__)


class Auth:
    """Represent the authentication manager."""

    def __init__(
        self,
        client_session: ClientSession,
        api_key: str,
        shared_secret: str,
        auth_token: str | None = None,
        permission: str = "delete",
    ) -> None:
        """Set up the auth manager."""
        self._client_session = client_session
        self.auth_token = auth_token
        self.permission = permission
        self.api_key = api_key
        self._shared_secret = shared_secret

    async def request(self, url: str, **kwargs: Any) -> ClientResponse:  # noqa: ANN401
        """Make a request."""
        headers: dict[str, Any] | None
        headers = {} if (headers := kwargs.get("headers")) is None else dict(headers)

        return await self._client_session.get(
            url,
            **kwargs,
            headers=headers,
        )

    async def authenticate_desktop(self) -> tuple[str, str]:
        """Authenticate as a desktop application."""
        data = await self.call_api("rtm.auth.getFrob", api_key=self.api_key)
        frob: str = data["frob"]
        url = self.generate_authorize_url(
            api_key=self.api_key,
            perms=self.permission,
            frob=frob,
        )
        return url, frob

    def generate_authorize_url(self, api_key: str, perms: str, frob: str) -> str:
        """Generate a URL for authorization."""
        params = {
            "api_key": api_key,
            "perms": perms,
            "frob": frob,
        }
        all_params = params | {"api_sig": self._sign_request(params)}
        return str(URL(AUTH_URL).with_query(all_params))

    async def get_token(self, frob: str) -> dict[str, Any]:
        """Fetch the authentication token with the frob."""
        data = await self.call_api("rtm.auth.getToken", api_key=self.api_key, frob=frob)
        auth_data: dict[str, Any] = data["auth"]
        self.auth_token = cast(str, auth_data["token"])
        return auth_data

    async def check_token(self) -> bool:
        """Check if auth token is valid."""
        if self.auth_token is None:
            return False
        try:
            await self.call_api_auth("rtm.auth.checkToken")
        except APIAuthError:
            return False

        return True

    async def call_api_auth(self, api_method: str, **params: Any) -> dict[str, Any]:  # noqa: ANN401
        """Call an api method that requires authentication."""
        if self.auth_token is None:
            raise RuntimeError("Missing authentication token.")
        all_params = {"api_key": self.api_key, "auth_token": self.auth_token} | params
        return await self.call_api(api_method, **all_params)

    async def call_api(self, api_method: str, **params: Any) -> dict[str, Any]:  # noqa: ANN401
        """Call an api method."""
        # Remove empty values.
        params = {key: value for key, value in params.items() if value is not None}
        all_params = {"method": api_method} | params | {"format": "json"}
        all_params |= {"api_sig": self._sign_request(all_params)}
        response = await self.request(REST_URL, params=all_params)

        try:
            response.raise_for_status()
        except ClientResponseError as err:
            if err.status in (HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED):
                raise TransportAuthError(err) from err
            raise TransportResponseError(err) from err

        response_text = await response.text()

        if "rtm.auth" not in api_method:
            logged_response_text = response_text
            if self.api_key in response_text:
                logged_response_text = response_text.replace(self.api_key, "API_KEY")
            _LOGGER.debug("Response text: %s", logged_response_text)

        # API doesn't return a JSON encoded response.
        # It's text/javascript mimetype but with a JSON string in the text.
        data: dict[str, Any] = json.loads(response_text)["rsp"]

        if data["stat"] == "fail":
            error_response = BaseErrorResponse.from_dict(data)
            code = error_response.err.code
            if 98 <= code <= 100:
                raise APIAuthError(code, error_response.err.msg)
            raise APIResponseError(code, error_response.err.msg)
        return data

    def _sign_request(self, params: dict[str, Any]) -> str:
        """Return the string representing the signed request."""
        sorted_params = {key: params[key] for key in sorted(params)}
        param_string = "".join(
            f"{key}{val}" for key, val in sorted_params.items() if val is not None
        )
        data = f"{self._shared_secret}{param_string}".encode()
        return hashlib.md5(data).hexdigest()  # noqa: S324


class AioRTMClient:
    """Represent the aiortm client."""

    def __init__(
        self,
        auth: Auth,
    ) -> None:
        """Set up the client instance."""
        self.rtm = RTM(auth)
