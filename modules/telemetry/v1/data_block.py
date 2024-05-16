# Contains data block utilities for version 1 of the radio packet format
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Type
from enum import IntEnum
import struct

from modules.misc.converter import metres_to_feet, milli_degrees_to_celsius, pascals_to_psi


class BlockException(Exception):
    pass


class BlockUnknownException(BlockException):
    pass


class DataBlockException(BlockException):
    pass


class DataBlockUnknownException(BlockUnknownException):
    pass


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
    HUMIDITY = 0x08

    def __str__(self):
        match self:
            case DataBlockSubtype.DEBUG_MESSAGE:
                return "DEBUG MESSAGE"
            case DataBlockSubtype.ALTITUDE:
                return "ALTITUDE"
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
            case DataBlockSubtype.HUMIDITY:
                return "HUMIDITY"


class DataBlock(ABC):
    """The abstract base interface for all data blocks."""

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

    @abstractmethod
    def __str__(self):
        """Returns a string of the data block in a human-readable format"""
        pass

    @abstractmethod
    def __iter__(self):
        """Returns an iterator over the data block, typically used to get dictionaries"""
        pass

    @staticmethod
    def parse(block_subtype: DataBlockSubtype, payload: bytes) -> DataBlock:
        """Unmarshal a bytes object to appropriate block class."""

        SUBTYPE_CLASSES: dict[DataBlockSubtype, Type[DataBlock]] = {
            DataBlockSubtype.DEBUG_MESSAGE: DebugMessageDB,
            DataBlockSubtype.ALTITUDE: AltitudeDB,
            DataBlockSubtype.TEMPERATURE: TemperatureDB,
            DataBlockSubtype.PRESSURE: PressureDB,
            DataBlockSubtype.HUMIDITY: HumidityDB,
            DataBlockSubtype.ACCELERATION: LinearAccelerationDB,
            DataBlockSubtype.ANGULAR_VELOCITY: AngularVelocityDB,
        }

        subtype = SUBTYPE_CLASSES.get(block_subtype)

        if subtype is None:
            raise NotImplementedError

        return subtype.from_bytes(payload=payload)


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
        """
        Returns the iterator over the debug message
        """
        yield "mission_time", self.mission_time
        yield "message", self.message


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
        yield "mission_time", self.mission_time
        yield "altitude", {"metres": self.altitude, "feet": metres_to_feet(self.altitude)}


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
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, "
            f"temperature: {self.temperature} mC "
            f"({round(self.temperature / 1000, 1)}°C)"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "temperature", {"millidegrees": self.temperature, "celsius": milli_degrees_to_celsius(self.temperature)}


class PressureDB(DataBlock):
    """Represents a pressure data block."""

    def __init__(self, mission_time: int, pressure: int) -> None:
        """
        Constructs a pressure data block.

        Args:
            mission_time: The mission time the pressure was measured at in milliseconds since launch.
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
        yield "pressure", {"pascals": self.pressure, "psi": pascals_to_psi(self.pressure)}


class HumidityDB(DataBlock):
    """Represents a humidity data block."""

    def __init__(self, mission_time: int, humidity: int) -> None:
        """
        Constructs a humidity data block.

        Args:
            mission_time: The mission time the humidity was measured at in milliseconds since launch.
            humidity: The calculated relative humidity in ten thousandths of a percent.

        """
        super().__init__(mission_time)
        self.humidity: int = humidity

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a humidity data block from bytes.
        Returns:
            A humidity data block.
        """
        parts = struct.unpack("<II", payload)
        return cls(parts[0], parts[1])

    def __len__(self) -> int:
        """
        Get the length of a humidity data block in bytes.
        Returns:
            The length of a humidity data block in bytes, not including the block header.
        """
        return 8

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, humidity: {round(self.humidity / 100)}%"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "percentage", round(self.humidity / 100)

class LinearAccelerationDB(DataBlock):
    """Represents a linear acceleration data block"""

    def __init__(self, mission_time: int, x_axis: int, y_axis: int, z_axis: int) -> None:
        """
        Constructus a linear acceleration data block.
        
        Args:
            mission_time: The mission time the linear acceleration was measured in milliseconds since launch.
            x_axis: The acceleration about the x axis in meters per second squared.
            y_axis: The acceleration about the y axis in meters per second squared.
            z_axis: The acceleration about the z axis in meters per second squared.
            
        """
        super().__init__(mission_time)
        self.x_axis: int = x_axis
        self.y_axis: int = y_axis
        self.z_axis: int = z_axis

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a linear acceleration data block from bytes.
        Returns:
            A linear acceleration data block.
        """
        parts = struct.unpack("<Ihhh", payload)
        return cls(parts[0], parts[1] / 100, parts[2] / 100, parts[3] / 100)
    
    def __len__(self) -> int:
        """
        Get the length of a linear acceleration data block in bytes
        Returns:
            The length of a linear acceleration data block in bytes not including the block header.
        """
        return 10
    
    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, x-axis: {self.x_axis} m/s^2, y-axis: {self.y_axis} m/s^2, z-axis: {self.z_axis} m/s^2"
    
    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "acceleration", {"x_axis": self.x_axis, "y_axis": self.y_axis, "z_axis": self.z_axis}

class AngularVelocityDB(DataBlock):
    """Represents an angular velocity data block"""

    def __init__(self, mission_time: int, x_axis: int, y_axis: int, z_axis: int) -> None:
        """
        Constructus an angular velocity data block.
        
        Args:
            mission_time: The mission time the angular velocity was measured in milliseconds since launch.
            x_axis: The velocity about the x axis in degrees per second.
            y_axis: The velocity about the y axis in degrees per second.
            z_axis: The velocity about the z axis in degrees per second.
            
        """
        super().__init__(mission_time)
        self.x_axis: int = x_axis
        self.y_axis: int = y_axis
        self.z_axis: int = z_axis

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs an angular velocity data block from bytes.
        Returns:
            An angular velocity data block.
        """
        parts = struct.unpack("<Ihhh", payload)
        return cls(parts[0], parts[1] / 10, parts[2] / 10, parts[3] / 10)
    
    def __len__(self) -> int:
        """
        Get the length of an angular velocity data block in bytes
        Returns:
            The length of an angular velocity data block in bytes not including the block header.
        """
        return 10
    
    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, x-axis: {self.x_axis} dps, y-axis: {self.y_axis} dps, z-axis: {self.z_axis} dps"
    
    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "velocity", {"x_axis": self.x_axis, "y_axis": self.y_axis, "z_axis": self.z_axis}

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
        case DataBlockSubtype.DEBUG_MESSAGE:
            return DebugMessageDB.from_bytes(payload)
        case DataBlockSubtype.ALTITUDE:
            return AltitudeDB.from_bytes(payload)
        case DataBlockSubtype.TEMPERATURE:
            return TemperatureDB.from_bytes(payload)
        case DataBlockSubtype.PRESSURE:
            return PressureDB.from_bytes(payload)
        case DataBlockSubtype.HUMIDITY:
            return HumidityDB.from_bytes(payload)
        case DataBlockSubtype.ACCELERATION:
            return LinearAccelerationDB.from_bytes(payload)
        case DataBlockSubtype.ANGULAR_VELOCITY:
            return AngularVelocityDB.from_bytes(payload)
        case _:
            raise NotImplementedError
