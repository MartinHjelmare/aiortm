"""Provide a model for contacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mashumaro.mixins.json import DataClassJSONMixin

from .response import BaseResponse, TransactionResponse

if TYPE_CHECKING:
    from ..client import Auth


@dataclass
class ContactResponse(DataClassJSONMixin):
    """Represent a response for a contact."""

    id: int
    fullname: str
    username: str


@dataclass
class ContactAddResponse(BaseResponse):
    """Represent a response for add contact."""

    transaction: TransactionResponse
    contact: ContactResponse


@dataclass
class ContactsResponse(BaseResponse):
    """Represent a response for a list of contacts."""

    # The API inconsistently returns an empty list when no contacts are present.
    contacts: list[ContactResponse]

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Ensure that contacts is a list of contacts."""
        contacts = d["contacts"]
        if isinstance(contacts, dict):
            d["contacts"] = contacts["contact"]
        return d


@dataclass
class ContactDeleteResponse(BaseResponse):
    """Represent a response for delete contact."""

    transaction: TransactionResponse


@dataclass
class Contacts:
    """Represent the contacts model."""

    api: Auth

    async def add(self, timeline: int, contact: str) -> ContactAddResponse:
        """Add a contact."""
        result = await self.api.call_api_auth(
            "rtm.contacts.add", timeline=timeline, contact=contact
        )
        return ContactAddResponse.from_dict(result)

    async def delete(self, timeline: int, contact_id: int) -> ContactDeleteResponse:
        """Delete a contact."""
        result = await self.api.call_api_auth(
            "rtm.contacts.delete", timeline=timeline, contact_id=contact_id
        )
        return ContactDeleteResponse.from_dict(result)

    async def get_list(self) -> ContactsResponse:
        """Get a list of contacts."""
        result = await self.api.call_api_auth("rtm.contacts.getList")
        return ContactsResponse.from_dict(result)
