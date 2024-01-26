"""Provide a model for the RTM API."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .contacts import Contacts
from .tasks import Tasks
from .timelines import Timelines

if TYPE_CHECKING:
    from ..client import Auth


@dataclass
class RTM:
    """Represent the rtm model."""

    api: "Auth"
    contacts: "Contacts" = field(init=False)
    tasks: "Tasks" = field(init=False)
    timelines: "Timelines" = field(init=False)

    def __post_init__(self) -> None:
        """Set up the instance."""
        self.contacts = Contacts(self.api)
        self.tasks = Tasks(self.api)
        self.timelines = Timelines(self.api)
