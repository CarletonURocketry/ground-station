# Contains universal block utilities for version 1 of the radio packet format
from dataclasses import dataclass
from enum import IntEnum
from typing import Self, Optional
import struct
import logging

from modules.telemetry.v1.data_block import DataBlockSubtype

MIN_SUPPORTED_VERSION: int = 1
MAX_SUPPORTED_VERSION: int = 1

# Set up logging
logger = logging.getLogger(__name__)


class BlockType(IntEnum):
    """The different radio block types for version 1 of the radio packet format."""

    ALTITUDE_ABOVE_SEA_LEVEL = 0x0
    ALTITUDE_ABOVE_LAUNCH_LEVEL = 0x01
    TEMPERATURE = 0x02
    PRESSURE = 0x03
    LINEAR_ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x06
    HUMIDITY = 0x07
    COORDINATES = 0x08
    VOLTAGE = 0x09

class UnsupportedEncodingVersionError(Exception):
    """Exception raised when the encoding version is not supported."""

    def __init__(self, version: int):
        self.version = version
        super().__init__(f"Unsupported encoding version: {version}")


class InvalidHeaderFieldValueError(Exception):
    """Exception raised when an invalid header field is encountered."""

    def __init__(self, cls_name: str, val: str, field: str):
        self.val = val
        self.field = field
        super().__init__(f"Invalid {cls_name} field: {val} is not a valid value for {field}")


@dataclass
class PacketHeader:
    """Represents a V2 packet header."""
    callsign: str
    timestamp: int
    num_blocks: int
    packet_num: int

@dataclass
class BlockHeader:
    """Represents a V2 header for a telemetry block."""
    type: BlockType

#Parse packet header
def parse_packet_header(header_bytes: bytes) -> PacketHeader:
    callsign_bytes = header_bytes[:9]
    callsign = ''
    for c in callsign_bytes:
       callsign += chr(c) 
    timestamp, num_blocks, packet_num = struct.unpack("<H", header_bytes[9:])
    return PacketHeader(callsign, timestamp, num_blocks, packet_num)

#Parse block header
def parse_block_header(header_bytes: bytes) -> BlockHeader:
    type = struct.unpack("<B", header_bytes)
    return BlockHeader(BlockType(type))
