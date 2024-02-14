# Contains universal block utilities for version 1 of the radio packet format
from enum import IntEnum


class BlockType(IntEnum):
    """The different radio block types for version 1 of the radio packet format."""
    DATA = 0x0
    RESERVED = 0xFF


class DeviceAddress(IntEnum):
    """Lists the different device addresses for version 1 of the radio packet format."""

    GROUND_STATION = 0x0
    ROCKET = 0x1
    RESERVED = 0xFE
    MULTICAST = 0xFF

    def __str__(self):
        match self:
            case DeviceAddress.GROUND_STATION:
                return "GROUND STATION"
            case DeviceAddress.ROCKET:
                return "ROCKET"
            case DeviceAddress.RESERVED:
                return "RESERVED"
            case DeviceAddress.MULTICAST:
                return "MULTICAST"
