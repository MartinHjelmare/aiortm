"""Provide a base response model."""

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from mashumaro.mixins.json import DataClassJSONMixin

StatT = TypeVar("StatT", bound=Literal["ok", "fail"], default=Literal["ok", "fail"])


@dataclass
class BaseResponse(DataClassJSONMixin, Generic[StatT]):
    """Represent a base response."""

    stat: StatT


@dataclass
class ErrorResponse(DataClassJSONMixin):
    """Represent the error response."""

    code: int
    msg: str


@dataclass
class BaseErrorResponse(BaseResponse[Literal["fail"]]):
    """Represent a base error response."""

    err: ErrorResponse


@dataclass
class TransactionResponse(DataClassJSONMixin):
    """Represent a transaction response."""

    id: int
    undoable: int
