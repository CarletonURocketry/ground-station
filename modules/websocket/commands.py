# Contains the websocket command structure
__author__ = "Matteo Golin"

# Imports
from enum import StrEnum, Enum, EnumType
import enum


# Classes
class WebsocketCommandNotFound(Exception):
    """Raised when there is no matching command."""

    def __init__(self, command: str):
        self.command = command
        self.message = f"The websocket command {command} does not exist."
        super().__init__(self.message)


class WebsocketCommand(Enum):
    """Contains the structure for the telemetry commands."""

    UPDATE: str = "update"

    @enum.member
    class REPLAY(StrEnum):
        """Contains the structure for the replay subcommands."""

        PLAY: str = "play replay"
        PAUSE: str = "pause replay"
        SPEED: str = "speed replay"
        STOP: str = "stop replay"

    @enum.member
    class RECORD(StrEnum):
        """Contains the structure for the record subcommands."""

        START: str = "start recording"
        STOP: str = "stop recording"


# Parsing functions
def parse(websocket_command: list[str], enum: EnumType) -> Enum:
    """
    Returns the websocket command as the matching command enum variable. Any remaining parameters will be left
    inside the websocket_command list parameter.
    """

    sub_command = websocket_command.pop(0)  # Get the highest level command

    try:
        next_enum = enum[sub_command.upper()]
    except KeyError:
        raise WebsocketCommandNotFound(sub_command)

    if websocket_command and type(next_enum.value) is not str:
        return parse(websocket_command, enum=next_enum.value)
    else:
        return next_enum
