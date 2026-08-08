"""Provide a model for lists."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mashumaro import field_options
from mashumaro.mixins.json import DataClassJSONMixin

from .response import BaseResponse, TransactionResponse

if TYPE_CHECKING:
    from aiortm.client import Auth


@dataclass
class ListResponse(DataClassJSONMixin):
    """Represent a response for a list."""

    id: int
    name: str
    deleted: bool
    locked: bool
    archived: bool
    position: int
    smart: bool
    list_filter: str | None = field(
        metadata=field_options(alias="filter"),
        default=None,
    )
    sort_order: int | None = field(
        default=None,
    )

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Convert RTM flag strings to booleans."""
        for key in ("deleted", "locked", "archived", "smart"):
            if key in d:
                d[key] = d[key] == "1"
        return d


@dataclass
class ListsResponse(BaseResponse):
    """Represent a response for a list of lists."""

    lists: list[ListResponse]

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Ensure that lists is a list of list items."""
        lists_data = d["lists"]
        if isinstance(lists_data, dict):
            list_data = lists_data.get("list", [])
            if isinstance(list_data, dict):
                list_data = [list_data]
            d["lists"] = list_data
        return d


@dataclass
class ListAddResponse(BaseResponse):
    """Represent a response for add list."""

    transaction: TransactionResponse
    added_list: ListResponse = field(metadata=field_options(alias="list"))


@dataclass
class Lists:
    """Represent the lists model."""

    api: Auth

    async def get_list(self) -> ListsResponse:
        """Get a list of lists."""
        result = await self.api.call_api_auth("rtm.lists.getList")
        return ListsResponse.from_dict(result)

    async def add(self, *, timeline: int, name: str) -> ListAddResponse:
        """Add a list."""
        result = await self.api.call_api_auth(
            "rtm.lists.add",
            timeline=timeline,
            name=name,
        )
        return ListAddResponse.from_dict(result)
