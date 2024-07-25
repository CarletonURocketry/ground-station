# Contains the websocket command structure
__author__ = "Matteo Golin"

# Imports
from enum import StrEnum, Enum
from typing import Type


# Classes
class WebsocketCommandNotFound(Exception):
    """Raised when there is no matching command."""

    def __init__(self, command: str):
        self.command = command
        self.message = f"The websocket command '{command}' does not exist."
        super().__init__(self.message)


class ReplayCommands(StrEnum):
    """Contains the structure for the replay subcommands."""

    PLAY = "play replay"
    PAUSE = "pause replay"
    RESUME = "resume replay"
    SPEED = "speed replay"
    STOP = "stop replay"


class RecordCommands(StrEnum):
    """Contains the structure for the record subcommands."""

    START = "start recording"
    STOP = "stop recording"


class WebsocketCommand(Enum):
    """Contains the structure for the telemetry commands."""

    UPDATE = "update"
    RECORD = RecordCommands
    REPLAY = ReplayCommands


# Parsing functions
def split_command_string(command: str) -> list[str]:
    """Splits a websocket command on the spaces."""
    return command.split(" ")


def parse(websocket_command: list[str], enum: Type[Enum] = WebsocketCommand) -> Enum:
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
