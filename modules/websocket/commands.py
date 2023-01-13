# Contains the websocket command structure
__author__ = "Matteo Golin"

# Imports
from enum import StrEnum, Enum


# Classes
class RecordCommands(StrEnum):

    """Contains the structure for the record subcommands."""

    START: str = "start"
    STOP: str = "stop"


class ReplayCommands(StrEnum):

    """Contains the structure for the replay subcommands."""

    PLAY: str = "play"
    PAUSE: str = "pause"
    SPEED: str = "speed"
    STOP: str = "stop"


class TelemetryCommands(Enum):

    """Contains the structure for the telemetry commands."""

    UPDATE: str = "update"
    REPLAY: StrEnum = ReplayCommands
    RECORD: StrEnum = RecordCommands


if __name__ == '__main__':
    command = "replay pause".split()
    print(TelemetryCommands.REPLAY == command[0])

