from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
import struct

from modules.telemetry.packet_spec.headers import *


@dataclass
class Block(ABC):
    measurement_time: int


@dataclass
class AltitudeAboveLaunchLevel(Block):
    altitude: int


@dataclass
class AltitudeAboveSeaLevel(Block):
    altitude: int


@dataclass
class LinearAcceleration(Block):
    x_axis: int
    y_axis: int
    z_axis: int


@dataclass
class AngularVelocity(Block):
    x_axis: int
    y_axis: int
    z_axis: int


@dataclass
class Coordinates(Block):
    latitude: int
    longitude: int


@dataclass
class Humidity(Block):
    humidity: int


@dataclass
class Pressure(Block):
    pressure: int


@dataclass
class Temperature(Block):
    temperature: int


@dataclass
class Voltage(Block):
    voltage: int
    id: int


class InvalidBlockContents(Exception):
    """Exception raised when invalid block contents are encountered"""

    def __init__(self, block_type: str, message: str = ""):
        self.block_type = block_type
        super().__init__(f"Invalid block for {block_type}: {message}")


def get_timestamp(packet_header: PacketHeader, offset_timestamp: int) -> int:
    """Turns the relative timestamp in a block into an absolute timestamp relative to mission start"""
    return (packet_header.timestamp * 30 * 1000) + offset_timestamp


# Parsing the packet message
def parse_block_contents(packet_header: PacketHeader, block_header: BlockHeader, encoded: bytes) -> Block:
    """Parses the block contents and returns an appropriate block

    Args:
        packet_header (PacketHeader): The header of the packet this block was recieved in
        block_header (BlockHeader): The header of the block to parse from the contents
        encoded (bytes): The encoded block body to parse

    Raises:
        InvalidBlockContents: If the block body could not be parsed correctly

    Returns:
        Block: The parsed block, either a Block or one of its subtypes
    """
    try:
        match block_header.type:
            case BlockType.ALTITUDE_ABOVE_SEA_LEVEL:
                offset_timestamp, altitude = struct.unpack("<Hi", encoded)
                return AltitudeAboveSeaLevel(get_timestamp(packet_header, offset_timestamp), altitude)

            case BlockType.ALTITUDE_ABOVE_LAUNCH_LEVEL:
                offset_timestamp, altitude = struct.unpack("<Hi", encoded)
                return AltitudeAboveLaunchLevel(get_timestamp(packet_header, offset_timestamp), altitude)

            case BlockType.TEMPERATURE:
                offset_timestamp, temperature = struct.unpack("<Hi", encoded)
                return Temperature(get_timestamp(packet_header, offset_timestamp), temperature)

            case BlockType.PRESSURE:
                offset_timestamp, pressure = struct.unpack("<HI", encoded)
                return Pressure(get_timestamp(packet_header, offset_timestamp), pressure)

            case BlockType.LINEAR_ACCELERATION:
                offset_timestamp, x_axis, y_axis, z_axis = struct.unpack("<HHHH", encoded)
                return LinearAcceleration(get_timestamp(packet_header, offset_timestamp), x_axis, y_axis, z_axis)

            case BlockType.ANGULAR_VELOCITY:
                offset_timestamp, x_axis, y_axis, z_axis = struct.unpack("<HHHH", encoded)
                return AngularVelocity(get_timestamp(packet_header, offset_timestamp), x_axis, y_axis, z_axis)

            case BlockType.HUMIDITY:
                offset_timestamp, humidity = struct.unpack("<HI", encoded)
                return Humidity(get_timestamp(packet_header, offset_timestamp), humidity)

            case BlockType.VOLTAGE:
                offset_timestamp, voltage, identifier = struct.unpack("<HiB", encoded)
                return Voltage(get_timestamp(packet_header, offset_timestamp), voltage, identifier)

            case BlockType.COORDINATES:
                offset_timestamp, latitude, longitude = struct.unpack("<Hii", encoded)
                return Coordinates(get_timestamp(packet_header, offset_timestamp), latitude, longitude)
    except struct.error as e:
        raise InvalidBlockContents(block_header.type.name, f"bad block contents: {e}")
