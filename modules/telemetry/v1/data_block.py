# Contains data block utilities for version 1 of the radio packet format
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Type
from enum import IntEnum
import struct
from modules.telemetry.block import BlockException, BlockUnknownException


class DataBlockSubtype(IntEnum):
    """Lists the subtypes of data blocks that can be sent in Version 1 of the packet encoding format."""

    DEBUG_MESSAGE = 0x00
    ALTITUDE = 0x01
    TEMPERATURE = 0x02
    PRESSURE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS_LOCATION = 0x06
    GNSS_METADATA = 0x07
    RESERVED = 0x3F

    def __str__(self):
        match self:
            case DataBlockSubtype.DEBUG_MESSAGE:
                return "DEBUG MESSAGE"
            case DataBlockSubtype.ALTITUDE:
                return "ANGULAR VELOCITY"
            case DataBlockSubtype.TEMPERATURE:
                return "TEMPERATURE"
            case DataBlockSubtype.PRESSURE:
                return "PRESSURE"
            case DataBlockSubtype.ACCELERATION:
                return "ACCELERATION"
            case DataBlockSubtype.ANGULAR_VELOCITY:
                return "ANGULAR VELOCITY"
            case DataBlockSubtype.GNSS_LOCATION:
                return "GNSS LOCATION"
            case DataBlockSubtype.GNSS_METADATA:
                return "GNSS METADATA"
            case _:
                return "RESERVED"


class DataBlockException(BlockException):
    pass


class DataBlockUnknownException(BlockUnknownException):
    pass


class DataBlock(ABC):
    """The base interface for all data blocks."""

    def __init__(self, mission_time: int) -> None:
        """Constructs a data block with the given mission time."""
        self.mission_time: int = mission_time

    @classmethod
    @abstractmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a data block from bytes.
        Returns:
            A new data block.
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Get the length of a data block in bytes.
        Returns:
            The length of a data block in bytes, not include the block header.
        """
        pass

    @staticmethod
    def parse(block_subtype: DataBlockSubtype, payload: bytes) -> DataBlock:
        """Unmarshal a bytes object to appropriate block class."""

        SUBTYPE_CLASSES: dict[DataBlockSubtype, Type[DataBlock]] = {
            DataBlockSubtype.DEBUG_MESSAGE: DebugMessageDB,
            DataBlockSubtype.ALTITUDE: AltitudeDB,
            DataBlockSubtype.TEMPERATURE: TemperatureDB,
            DataBlockSubtype.PRESSURE: PressureDB,
        }

        subtype = SUBTYPE_CLASSES.get(block_subtype)

        if subtype is None:
            raise DataBlockUnknownException(f"Unknown data block subtype: {block_subtype} {payload} {payload.hex()}")

        return subtype.from_bytes(payload=payload)


class AltitudeDB(DataBlock):
    """Represents an altitude data block."""

    def __init__(self, mission_time: int, altitude: int) -> None:
        super().__init__(mission_time)
        self.altitude = altitude

    def __len__(self) -> int:
        """
        Get the length of an altitude data block in bytes.
        Returns:
            The length of an altitude data block in bytes, not including the block header.
        """
        return 16

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a data block from bytes.
        Returns:
            An altitude data block.
        """

        parts = struct.unpack("<Ii", payload)
        return cls(parts[0], parts[1] / 1000)  # Altitude is sent in mm

    def to_bytes(self) -> bytes:
        return struct.pack("<Ii", int(self.altitude))

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, altitude: {self.altitude} m"

    def __iter__(self):
        yield "mission time", self.mission_time
        yield "altitude", {"meters": self.altitude}


class PressureDB(DataBlock):
    """Represents a pressure data block."""

    def __init__(self, mission_time: int, pressure: int) -> None:
        """
        Constructs a pressure data block.

        Args:
            mission_time: The mission time the altitude was measured at in milliseconds since launch.
            pressure: The pressure in millibars.

        """
        super().__init__(mission_time)
        self.pressure: int = pressure

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a pressure data block from bytes.
        Returns:
            A pressure data block.
        """
        parts = struct.unpack("<II", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a pressure data block in bytes.
        Returns:
            The length of a pressure data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, pressure: {self.pressure} Pa"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "pressure", {"pascals": self.pressure}


class TemperatureDB(DataBlock):
    """Represents a temperature data block."""

    def __init__(self, mission_time: int, temperature: int) -> None:
        super().__init__(mission_time)
        self.temperature: int = temperature

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a temperature data block from bytes.
        Returns:
            A temperature data block.
        """
        parts = struct.unpack("<Ii", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a temperature data block in bytes.
        Returns:
            The length of a temperature data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, temperature: {self.temperature} mC"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "temperature", {"millidegrees": self.temperature, "celsius": round(self.temperature / 1000, 2)}


class DebugMessageDB(DataBlock):
    """Represents a debug message data block."""

    def __init__(self, mission_time: int, message: str) -> None:
        super().__init__(mission_time)
        self.message: str = message

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a debug message data block from bytes.
        Returns:
            A debug message data block.
        """
        mission_time = struct.unpack("<I", payload[:4])[0]
        message = payload[4:].decode("utf-8")
        return cls(mission_time, message)

    def __len__(self) -> int:
        """
        Get the length of a debug message data block in bytes.
        Returns:
            The length of a debug message data block in bytes, not including the block header.
        """
        return 4 + len(self.message)

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, message: {self.message}"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "message", self.message


def parse_data_block(type: DataBlockSubtype, payload: bytes) -> DataBlock:
    """
    Parses a bytes payload into the correct data block type.
    Args:
        type: The type of data block to parse the bytes into.
        payload: The bytes payload to parse into a data block.
    Returns:
        The parse data block.
    Raises:
        ValueError: Raised if the bytes cannot be parsed into the corresponding type.
    """

    match type:
        case DataBlockSubtype.ALTITUDE:
            return AltitudeDB.from_bytes(payload)
        case DataBlockSubtype.PRESSURE:
            return PressureDB.from_bytes(payload)
        case DataBlockSubtype.TEMPERATURE:
            return TemperatureDB.from_bytes(payload)
        case DataBlockSubtype.DEBUG_MESSAGE:
            return DebugMessageDB.from_bytes(payload)
        case _:
            raise NotImplementedError
