# Contains the websocket command structure
__author__ = "Matteo Golin"

# Imports
from enum import StrEnum, Enum, EnumType


# Classes
class WebsocketCommandNotFound(Exception):

    """Raised when there is no matching command."""

    def __init__(self, command: str):
        self.command = command
        self.message = f"The websocket command {command} does not exist.."
        super().__init__(self.message)


class RecordCommand(StrEnum):

    """Contains the structure for the record subcommands."""

    START: str = "start recording"
    STOP: str = "stop recording"


class ReplayCommand(StrEnum):

    """Contains the structure for the replay subcommands."""

    PLAY: str = "play replay"
    PAUSE: str = "pause replay"
    SPEED: str = "speed replay"
    STOP: str = "stop replay"


class TelemetryCommand(Enum):

    """Contains the structure for the telemetry commands."""

    UPDATE: str = "update"
    REPLAY: ReplayCommand = ReplayCommand
    RECORD: RecordCommand = RecordCommand


# Parsing functions
def parse(websocket_command: list[str], enum: EnumType) -> Enum:

    """Parses the websocket command into the command structure."""

    command = websocket_command.pop(0)  # Get the highest level command

    try:
        next_enum = enum[command.upper()]
        print(next_enum)
    except KeyError:
        raise WebsocketCommandNotFound(command)

    if websocket_command:
        return parse(websocket_command, enum=next_enum.value)
    else:
        return next_enum


if __name__ == '__main__':

    commands = "replay play".split()
    command = parse(commands, TelemetryCommand)

