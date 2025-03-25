from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
import struct

from modules.telemetry.packet_spec.headers import *


class Block(ABC):
    # A format for the struct class to unpack the block from bytes
    _struct_format: str
    # Labels for the unpacked values returned by struct.unpack, in order
    _unpacked_labels: tuple[str, ...]

    @classmethod
    def _decode(cls, encoded: bytes) -> dict[str, int | str]:
        """Decode this block from a byte string

        Args:
            encoded (bytes): The bytes to use to decode this block

        Returns:
            dict[str, int | str]: A dictionary mapping values from _unpacked_labels to the returned struct data
        """
        unpacked: dict[str, int | str] = dict()
        for label, val in zip(cls._unpacked_labels, struct.unpack(cls._struct_format, encoded)):
            unpacked[label] = val
        return unpacked

    @classmethod
    def __len__(cls) -> int:
        """Use the struct format string to get the length of this block

        Returns:
            int: The length of this block in bytes
        """
        return struct.calcsize(cls._struct_format)

    @classmethod
    def convert_timestamp(cls, abs_time: int, offset: int) -> int:
        """Convert an offset timestamp to an absolute timestamp

        Args:
            abs_time (int): The absolute timestamp to use as reference
            offset (int): The offset from this timestamp to convert

        Returns:
            int: The absolute timestamp of this block
        """
        return abs_time + offset

    def __init__(self, encoded: bytes, abs_time: int = 0):
        """Initialize this block by decoding it from a byte string

        Args:
            encoded (bytes): The encoded block
            abs_time (int, optional): If this block has a measurement_time field, use this value as the absolute mission time that this should be offset from. Defaults to 0.
        """
        self._unpacked = self._decode(encoded)
        if "measurement_time" in self._unpacked:
            self._unpacked["measurement_time"] = self.convert_timestamp(
                abs_time, int(self._unpacked["measurement_time"])
            )

    def get_data(self) -> dict[str, int | str]:
        """Get the unpacked data from this block

        Returns:
            dict[str, int | str]: The unpacked data from this block
        """
        return self._unpacked


@dataclass
class AltitudeAboveLaunchLevel(Block):
    _struct_format: str = "<Hi"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "altitude")


@dataclass
class AltitudeAboveSeaLevel(Block):
    _struct_format: str = "<Hi"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "altitude")


@dataclass
class LinearAcceleration(Block):
    _struct_format: str = "<HHHH"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "x_axis", "y_axis", "z_axis")


@dataclass
class AngularVelocity(Block):
    _struct_format: str = "<HHHH"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "x_axis", "y_axis", "z_axis")


@dataclass
class Coordinates(Block):
    _struct_format: str = "<Hii"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "latitude", "longitude")


@dataclass
class Humidity(Block):
    _struct_format: str = "<HI"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "humidity")


@dataclass
class Pressure(Block):
    _struct_format: str = "<HI"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "pressure")


@dataclass
class Temperature(Block):
    _struct_format: str = "<Hi"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "temperature")


@dataclass
class Voltage(Block):
    _struct_format: str = "<HiB"
    _unpacked_labels: tuple[str, ...] = ("measurement_time", "voltage", "identifier")


class InvalidBlockContents(Exception):
    """Exception raised when invalid block contents are encountered"""

    def __init__(self, block_type: str, message: str = ""):
        self.block_type = block_type
        super().__init__(f"Invalid block for {block_type}: {message}")


def get_block_class(type: BlockType) -> type[Block]:
    """Get the block class associated with this type

    Args:
        type (BlockType): The type to get the block class for

    Raises:
        ValueError: If the block type is not supported

    Returns:
        type[Block]: The class of the block associated with this type
    """
    match type:
        case BlockType.ALTITUDE_ABOVE_LAUNCH_LEVEL:
            return AltitudeAboveLaunchLevel
        case BlockType.ALTITUDE_ABOVE_SEA_LEVEL:
            return AltitudeAboveSeaLevel
        case BlockType.LINEAR_ACCELERATION:
            return LinearAcceleration
        case BlockType.ANGULAR_VELOCITY:
            return AngularVelocity
        case BlockType.COORDINATES:
            return Coordinates
        case BlockType.HUMIDITY:
            return Humidity
        case BlockType.PRESSURE:
            return Pressure
        case BlockType.TEMPERATURE:
            return Temperature
        case BlockType.VOLTAGE:
            return Voltage
        case _:
            raise ValueError(f"Unsupported block type: {type}")


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
        block_class = get_block_class(block_header.type)
        return block_class(encoded, packet_header.timestamp)
    except struct.error as e:
        raise InvalidBlockContents(block_header.type.name, f"bad block contents: {e}")
