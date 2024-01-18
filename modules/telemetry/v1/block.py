# Contains universal block utilities for version 1 of the radio packet format
from enum import IntEnum


class BlockType(IntEnum):
    """The different radio block types for version 1 of the radio packet format."""

    CONTROL = 0x0
    COMMAND = 0x1
    DATA = 0x2


class DeviceAddress(IntEnum):
    """Lists the different device addresses for version 1 of the radio packet format."""

    GROUND_STATION = 0x0
    ROCKET = 0x1
    MULTICAST = 0xF

    def __str__(self):
        match self:
            case DeviceAddress.GROUND_STATION:
                return "GROUND STATION"
            case DeviceAddress.ROCKET:
                return "ROCKET"
            case DeviceAddress.MULTICAST:
                return "MULTICAST"
