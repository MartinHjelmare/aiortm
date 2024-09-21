"""Provide a model for timelines."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .response import BaseResponse

if TYPE_CHECKING:
    from aiortm.client import Auth


@dataclass
class TimelineResponse(BaseResponse):
    """Represent a response for a timeline."""

    timeline: int


@dataclass
class Timelines:
    """Represent the timelines model."""

    api: "Auth"

    async def create(self) -> TimelineResponse:
        """Create a timeline."""
        result = await self.api.call_api_auth("rtm.timelines.create")
        return TimelineResponse.from_dict(result)
