"""Provide a model for contacts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, validator

from .response import BaseResponse, TransactionResponse

if TYPE_CHECKING:
    from ..client import Auth


class ContactResponse(BaseModel):
    """Represent a response for a contact."""

    id: int
    fullname: str
    username: str


class ContactAddResponse(BaseResponse):
    """Represent a response for add contact."""

    transaction: TransactionResponse
    contact: ContactResponse


class ContactsResponse(BaseResponse):
    """Represent a response for a list of contacts."""

    # The API inconsistently returns an empty list when no contacts are present.
    contacts: list[ContactResponse]

    @validator("contacts", pre=True)
    def ensure_list(  # pylint: disable=no-self-argument
        cls, value: list[Any] | dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """Ensure that contacts is a list of contacts."""
        if isinstance(value, dict):
            return value["contact"]
        return value


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
        return ContactAddResponse(**result)

    async def delete(self, timeline: int, contact_id: int) -> ContactDeleteResponse:
        """Delete a contact."""
        result = await self.api.call_api_auth(
            "rtm.contacts.delete", timeline=timeline, contact_id=contact_id
        )
        return ContactDeleteResponse(**result)

    async def get_list(self) -> ContactsResponse:
        """Get a list of contacts."""
        result = await self.api.call_api_auth("rtm.contacts.getList")
        return ContactsResponse(**result)
