# Contains data block utilities for version 1 of the radio packet format
from abc import ABC, abstractmethod
from typing import Self
from enum import IntEnum
import struct


class DataBlockSubtype(IntEnum):
    """Lists the sub types of data blocks that can be sent in Version 1 of the packet encoding format."""

    DEBUG_MESSAGE = 0x00
    ALTITUDE = 0x01
    TEMPERATURE = 0x01
    PRESSURE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS_LOCATION = 0x06
    GNSS_METADATA = 0x07


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

        parts = struct.unpack("<Iiii", payload)
        return AltitudeDB(parts[0])
    
    def to_bytes(self) -> bytes:
        return struct.pack("<Ii", int(self.altitude))

    def __str__(self):
        return (f"{self.__class__.__name__} -> time: {self.mission_time} ms, altitude: {self.altitude} m")

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
        return PressureDB(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a pressure data block in bytes.
        Returns:
            The length of a pressure data block in bytes, not including the block header.
        """
        return 8


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
        raise NotImplementedError

    def __len__(self) -> int:
        """
        Get the length of a temperature data block in bytes.
        Returns:
            The length of a temperature data block in bytes, not including the block header.
        """
        return 8


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
        raise NotImplementedError

    def __len__(self) -> int:
        """
        Get the length of a debug message data block in bytes.
        Returns:
            The length of a debug message data block in bytes, not including the block header.
        """
        return 4 + len(self.message)


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
