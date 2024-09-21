"""Provide exceptions raised by aiortm."""

from typing import Any

from aiohttp import ClientResponseError


class AioRTMError(Exception):
    """Represent an exception raised by aiortm."""


class ResponseError(AioRTMError):
    """Represent a bad response."""


class AuthError(ResponseError):
    """Represent a bad response."""


class APIResponseError(ResponseError):
    """Represent a bad response."""

    def __init__(self, code: int, msg: str, *args: Any) -> None:  # noqa: ANN401
        """Set up the instance."""
        super().__init__(msg, *args)
        self.code = code
        self.msg = msg


class TransportResponseError(ResponseError):
    """Represent a bad response."""

    def __init__(self, client_error: ClientResponseError, *args: Any) -> None:  # noqa: ANN401
        """Set up the instance."""
        super().__init__(client_error, *args)
        self.client_error = client_error


class APIAuthError(APIResponseError, AuthError):
    """Represent a failed authentication from the API."""


class TransportAuthError(TransportResponseError, AuthError):
    """Represent a failed authentication from the transport."""
