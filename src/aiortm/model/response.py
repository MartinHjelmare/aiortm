"""Provide a base response model."""
from typing import Literal

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Represent a base response."""

    stat: Literal["ok", "fail"]


class ErrorResponse(BaseModel):
    """Represent the error response."""

    code: int
    msg: str


class BaseErrorResponse(BaseResponse):
    """Represent a base error response."""

    stat: Literal["fail"]
    err: ErrorResponse


class TransactionResponse(BaseModel):
    """Represent a transaction response."""

    id: int
    undoable: int
