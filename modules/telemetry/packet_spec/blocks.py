from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field, fields
import struct

from modules.telemetry.packet_spec.headers import *


@dataclass
class Block:
    # A format for the struct class to unpack the block from bytes
    _struct_format: str = field(default="", init=False, repr=False)

    @classmethod
    def size(cls) -> int:
        """Use the struct format string to get the length of this block

        Returns:
            int: The length of this block in bytes
        """
        return struct.calcsize(cls._struct_format)

    @classmethod
    def decode(cls, encoded: bytes) -> tuple[int]:
        """Decode the block from bytes using the struct format string

        Returns:
            tuple[int]: The results of the unpacking
        """
        return struct.unpack(cls._struct_format, encoded)

    def asdict(self) -> dict[str, int]:
        """Convert the block to a dictionary of its fields

        Returns:
            dict[str, int]: The block as a dictionary
        """
        return {field.name: getattr(self, field.name) for field in fields(self) if field.repr}

    def __init__(self, *args):  # type: ignore
        """Stand-in for dataclass constructors with any number of arguments"""
        pass


@dataclass
class TimedBlock(Block):
    measurement_time: int


@dataclass
class AltitudeAboveLaunchLevel(TimedBlock):
    _struct_format: str = field(default="<Hi", init=False, repr=False)
    measurement_time: int
    altitude: int


@dataclass
class AltitudeAboveSeaLevel(TimedBlock):
    _struct_format: str = field(default="<Hi", init=False, repr=False)
    measurement_time: int
    altitude: int


@dataclass
class LinearAcceleration(TimedBlock):
    _struct_format: str = field(default="<HHHH", init=False, repr=False)
    measurement_time: int
    x_axis: int
    y_axis: int
    z_axis: int


@dataclass
class AngularVelocity(TimedBlock):
    _struct_format: str = field(default="<HHHH", init=False, repr=False)
    measurement_time: int
    x_axis: int
    y_axis: int
    z_axis: int


@dataclass
class Coordinates(TimedBlock):
    _struct_format: str = field(default="<Hii", init=False, repr=False)
    measurement_time: int
    latitude: int
    longitude: int


@dataclass
class Humidity(TimedBlock):
    _struct_format: str = field(default="<HI", init=False, repr=False)
    measurement_time: int
    humidity: int


@dataclass
class Pressure(TimedBlock):
    _struct_format: str = field(default="<HI", init=False, repr=False)
    measurement_time: int
    pressure: int


@dataclass
class Temperature(TimedBlock):
    _struct_format: str = field(default="<Hi", init=False, repr=False)
    measurement_time: int
    temperature: int


@dataclass
class Voltage(TimedBlock):
    _struct_format: str = field(default="<HiB", init=False, repr=False)
    measurement_time: int
    voltage: int
    identifier: int


class InvalidBlockContents(Exception):
    """Exception raised when invalid block contents are encountered"""

    def __init__(self, block_type: str, message: str = ""):
        self.block_type = block_type
        super().__init__(f"Invalid block for {block_type}: {message}")


def convert_timestamp(abs_time: int, block: Block):
    """Converts the absolute timestamp to the relative timestamp for the block

    Args:
        abs_time (int): The absolute timestamp
        block (Block): The block to convert the timestamp for, a subclass of TimedBlock
    """
    if isinstance(block, TimedBlock):
        block.measurement_time = abs_time + block.measurement_time


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
        # Leave the constructor up to dataclass
        block_class(*block_class.decode(encoded))
    except struct.error as e:
        raise InvalidBlockContents(block_header.type.name, f"bad block contents: {e}")
