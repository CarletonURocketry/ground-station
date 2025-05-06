# Contains universal block utilities for version 1 of the radio packet format
from dataclasses import dataclass
from enum import IntEnum
import struct
import logging

# Header lengths in bytes
PACKET_HEADER_LENGTH: int = 13
BLOCK_HEADER_LENGTH: int = 1
CALLSIGN_LENGTH: int = 9

# Set up logging
logger = logging.getLogger(__name__)


class BlockType(IntEnum):
    """The different radio block types"""

    ALTITUDE_ABOVE_SEA_LEVEL = 0x0
    ALTITUDE_ABOVE_LAUNCH_LEVEL = 0x01
    TEMPERATURE = 0x02
    PRESSURE = 0x03
    LINEAR_ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    HUMIDITY = 0x06
    COORDINATES = 0x07
    VOLTAGE = 0x08
    MAGNETIC_FIELD = 0x09


class InvalidHeaderFieldValueError(Exception):
    """Exception raised when an invalid header field is encountered."""

    def __init__(self, cls_name: str, val: str, field: str):
        self.val = val
        self.field = field
        super().__init__(f"Invalid {cls_name} field: {val} is not a valid value for {field}")


@dataclass
class PacketHeader:
    """Represents a packet header."""

    callsign: str
    timestamp: int
    num_blocks: int
    packet_num: int

    def __len__(self):
        return self.num_blocks


@dataclass
class BlockHeader:
    """Represents a header for a telemetry block."""

    type: BlockType


def parse_packet_header(header_bytes: bytes) -> PacketHeader:
    """Parses a packet header

    Args:
        header_bytes (bytes): The encoded packet header

    Raises:
        InvalidHeaderFieldValueError: If the packet header cannot be parsed and the packet should be ignored

    Returns:
        PacketHeader: A header containing information about the packet it accompanies
    """
    try:
        logger.debug(f"{header_bytes=}")
        callsign_bytes = header_bytes[:CALLSIGN_LENGTH]
        # valid headers should be in ascii, an error here is a problem
        callsign = callsign_bytes.decode("ascii", errors="replace")
        timestamp, num_blocks, packet_num = struct.unpack("<HBB", header_bytes[CALLSIGN_LENGTH:])
        return PacketHeader(callsign, timestamp, num_blocks, packet_num)
    except ValueError as e:
        raise InvalidHeaderFieldValueError(PacketHeader.__name__, header_bytes.hex(), f"bad packet header: {e}")


def parse_block_header(header_bytes: bytes) -> BlockHeader:
    """Parses a block header

    Args:
        header_bytes (bytes): The encoded block header

    Raises:
        InvalidHeaderFieldValueError: If the header cannot be parsed and the block should be ignored

    Returns:
        BlockHeader: A header containing information about the block it accompanies
    """
    try:
        logger.debug(f"{header_bytes=}")
        (type,) = struct.unpack("<B", header_bytes)
        return BlockHeader(BlockType(type))
    except (struct.error, ValueError) as e:
        raise InvalidHeaderFieldValueError(BlockHeader.__name__, header_bytes.hex(), f"bad block header: {e}")
