"""Provide a client for aiortm."""
from __future__ import annotations

import hashlib
from http import HTTPStatus
from typing import Any

from aiohttp import ClientResponse, ClientResponseError, ClientSession

from .exceptions import (
    APIAuthError,
    APIResponseError,
    TransportAuthError,
    TransportResponseError,
)

AUTH_URL = "https://www.rememberthemilk.com/services/auth/"
REST_URL = "https://api.rememberthemilk.com/services/rest/"


class Auth:
    """Represent the authentication manager."""

    def __init__(
        self,
        client_session: ClientSession,
        api_key: str,
        shared_secret: str,
        auth_token: str | None = None,
        permission: str = "write",
    ) -> None:
        """Set up the auth manager."""
        self._client_session = client_session
        self.auth_token = auth_token
        self.permission = permission
        self.api_key = api_key
        self._shared_secret = shared_secret

    async def request(self, url: str, **kwargs: Any) -> ClientResponse:
        """Make a request."""
        headers: dict[str, Any] | None = kwargs.get("headers")

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)

        return await self._client_session.get(
            url,
            **kwargs,
            headers=headers,
        )

    async def check_token(self) -> bool:
        """Check if auth token is valid."""
        if self.auth_token is None:
            return False
        try:
            await self._call_api(
                "rtm.auth.checkToken", api_key=self.api_key, auth_token=self.auth_token
            )
        except APIAuthError:
            return False

        return True

    async def _call_api_auth(self, api_method: str, **params: Any) -> dict[str, Any]:
        """Call an api method that requires authentication."""
        if self.auth_token is None:
            raise RuntimeError("Missing authentication token.")
        all_params = {"api_key": self.api_key, "auth_token": self.auth_token, **params}
        return await self._call_api(api_method, **all_params)

    async def _call_api(self, api_method: str, **params: Any) -> dict[str, Any]:
        """Call an api method."""
        params |= {"format": "json"}
        params |= {"api_sig": self._sign_request(params)}
        response = await self.request(REST_URL, method=api_method, **params)

        try:
            response.raise_for_status()
        except ClientResponseError as err:
            if err.status in (HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED):
                raise TransportAuthError(err) from err
            raise TransportResponseError(err) from err

        data: dict[str, Any] = (await response.json())["rsp"]

        if data["stat"] == "fail":
            code = data["err"]["code"]
            if 98 >= code <= 100:
                raise APIAuthError(code, data["err"]["msg"])
            raise APIResponseError(code, data["err"]["msg"])
        return data

    def _sign_request(self, params: dict[str, Any]) -> str:
        """Return the string representing the signed request."""
        sorted_params = {key: params[key] for key in sorted(params)}
        param_string = "".join(
            f"{key}{val}" for key, val in sorted_params.items() if val is not None
        )
        data = f"{self._shared_secret}{param_string}".encode()
        return hashlib.md5(data).hexdigest()  # nosec


class AioRTMClient:
    """Represent the aiortm client."""

    def __init__(
        self,
        auth: Auth,
    ) -> None:
        """Set up the client instance."""
        self.auth = auth
