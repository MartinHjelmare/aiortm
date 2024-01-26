"""Provide a base response model."""

from dataclasses import dataclass
from typing import Literal

from mashumaro.mixins.json import DataClassJSONMixin


@dataclass
class BaseResponse(DataClassJSONMixin):
    """Represent a base response."""

    stat: Literal["ok", "fail"]


@dataclass
class ErrorResponse(DataClassJSONMixin):
    """Represent the error response."""

    code: int
    msg: str


@dataclass
class BaseErrorResponse(BaseResponse):
    """Represent a base error response."""

    stat: Literal["fail"]
    err: ErrorResponse


@dataclass
class TransactionResponse(DataClassJSONMixin):
    """Represent a transaction response."""

    id: int
    undoable: int
