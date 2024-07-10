# Contains data block utilities for version 1 of the radio packet format
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Type
from enum import IntEnum
import struct

from modules.misc.converter import metres_to_feet, milli_degrees_to_celsius, pascals_to_psi


class DataBlockException(Exception):
    """Exception raised when an error occurs while parsing a data block."""

    def __init__(self, subtype_name: str, error: str):
        self.subtype_name = subtype_name
        self.error = error
        super().__init__(f"Error parsing {subtype_name} block: {error}")


class DataBlockSubtype(IntEnum):
    """Lists the subtypes of data blocks that can be sent in Version 1 of the packet encoding format."""

    DEBUG_MESSAGE = 0x00
    ALTITUDE_SEA_LEVEL = 0x01
    ALTITUDE_LAUNCH_LEVEL = 0x02
    TEMPERATURE = 0x03
    PRESSURE = 0x04
    LIN_ACCEL_REL = 0x05
    LIN_ACCEL_ABS = 0x06
    ANGULAR_VELOCITY = 0x07
    HUMIDITY = 0x08
    COORDINATES = 0x09
    VOLTAGE = 0x0A

    def __str__(self):
        match self:
            case DataBlockSubtype.DEBUG_MESSAGE:
                return "DEBUG MESSAGE"
            case DataBlockSubtype.ALTITUDE_SEA_LEVEL:
                return "SEA LEVEL ALTITUDE"
            case DataBlockSubtype.ALTITUDE_LAUNCH_LEVEL:
                return "LAUNCH LEVEL ALTITUDE"
            case DataBlockSubtype.TEMPERATURE:
                return "TEMPERATURE"
            case DataBlockSubtype.PRESSURE:
                return "PRESSURE"
            case DataBlockSubtype.LIN_ACCEL_REL:
                return "RELATIVE LINEAR ACCELERATION"
            case DataBlockSubtype.LIN_ACCEL_ABS:
                return "ABSOLUTE LINEAR ACCELERATION"
            case DataBlockSubtype.ANGULAR_VELOCITY:
                return "ANGULAR VELOCITY"
            case DataBlockSubtype.HUMIDITY:
                return "HUMIDITY"
            case DataBlockSubtype.COORDINATES:
                return "COORDINATES"
            case DataBlockSubtype.VOLTAGE:
                return "VOLTAGE"


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
            DataBlockSubtype.ALTITUDE_SEA_LEVEL: AltitudeSeaLevelDB,
            DataBlockSubtype.ALTITUDE_LAUNCH_LEVEL: AltitudeLaunchLevelDB,
            DataBlockSubtype.TEMPERATURE: TemperatureDB,
            DataBlockSubtype.PRESSURE: PressureDB,
            DataBlockSubtype.LIN_ACCEL_REL: RelativeLinearAccelerationDB,
            DataBlockSubtype.LIN_ACCEL_ABS: AbsoluteLinearAccelerationDB,
            DataBlockSubtype.ANGULAR_VELOCITY: AngularVelocityDB,
            DataBlockSubtype.HUMIDITY: HumidityDB,
            DataBlockSubtype.COORDINATES: CoordinatesDB,
            DataBlockSubtype.VOLTAGE: VoltageDB,
        }

        subtype = SUBTYPE_CLASSES.get(block_subtype)

        if subtype is None:
            raise NotImplementedError

        try:
            subtype_instance = subtype.from_bytes(payload)
        except Exception as e:
            raise DataBlockException(subtype.__name__, str(e))

        return subtype_instance


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


class AltitudeSeaLevelDB(AltitudeDB):
    """Represents an altitude data block with measurements relative to sea level."""

    def __init__(self, mission_time: int, altitude: int) -> None:
        super().__init__(mission_time, altitude)


class AltitudeLaunchLevelDB(AltitudeDB):
    """Represents an altitude data block with measurements relative to launch level."""

    def __init__(self, mission_time: int, altitude: int) -> None:
        super().__init__(mission_time, altitude)


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


class LinearAccelerationDB(DataBlock):
    """Represents a linear acceleration data block"""

    def __init__(self, mission_time: int, x_axis: int, y_axis: int, z_axis: int) -> None:
        """
        Constructs a linear acceleration data block.

        Args:
            mission_time: The mission time the linear acceleration was measured in milliseconds since launch.
            x_axis: The acceleration about the x axis in meters per second squared.
            y_axis: The acceleration about the y axis in meters per second squared.
            z_axis: The acceleration about the z axis in meters per second squared.
            magnitude: The magnitude of the linear acceleration in meters per second squared.
        """
        super().__init__(mission_time)
        self.x_axis: float = x_axis
        self.y_axis: float = y_axis
        self.z_axis: float = z_axis
        self.magnitude: float = round((abs(x_axis) ** 2 + abs(y_axis) ** 2 + abs(z_axis) ** 2) ** 0.5, 2)

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a linear acceleration data block from bytes.
        Returns:
            A linear acceleration data block.
        """
        parts = struct.unpack("<Ihhhh", payload)
        return cls(parts[0], parts[1] / 100, parts[2] / 100, parts[3] / 100)

    def __len__(self) -> int:
        """
        Get the length of a linear acceleration data block in bytes
        Returns:
            The length of a linear acceleration data block in bytes not including the block header.
        """
        return 10

    def __str__(self):
        return f"""{self.__class__.__name__} -> time: {self.mission_time} ms, x-axis: {self.x_axis} m/s^2, y-axis:
         {self.y_axis} m/s^2, z-axis: {self.z_axis} m/s^2, magnitude: {self.magnitude} m/s^2"""

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "linear_acceleration", {"x": self.x_axis, "y": self.y_axis, "z": self.z_axis, "magnitude": self.magnitude}


class RelativeLinearAccelerationDB(LinearAccelerationDB):
    """Represents a linear acceleration data block with measurements relative to the rocket's position."""

    def __init__(self, mission_time: int, x_axis: int, y_axis: int, z_axis: int) -> None:
        super().__init__(mission_time, x_axis, y_axis, z_axis)


class AbsoluteLinearAccelerationDB(LinearAccelerationDB):
    """Represents a linear acceleration data block with measurements relative to ground."""

    def __init__(self, mission_time: int, x_axis: int, y_axis: int, z_axis: int) -> None:
        super().__init__(mission_time, x_axis, y_axis, z_axis)


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
            magnitude: The magnitude of the angular velocity in degrees per second.
        """
        super().__init__(mission_time)
        self.x_axis: float = x_axis
        self.y_axis: float = y_axis
        self.z_axis: float = z_axis
        self.magnitude: float = round((abs(x_axis) ** 2 + abs(y_axis) ** 2 + abs(z_axis) ** 2) ** 0.5, 2)

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs an angular velocity data block from bytes.
        Returns:
            An angular velocity data block.
        """
        parts = struct.unpack("<Ihhhh", payload)
        return cls(parts[0], parts[1] / 10, parts[2] / 10, parts[3] / 10)

    def __len__(self) -> int:
        """
        Get the length of an angular velocity data block in bytes
        Returns:
            The length of an angular velocity data block in bytes not including the block header.
        """
        return 10

    def __str__(self):
        return f"""{self.__class__.__name__} -> time: {self.mission_time} ms, x-axis: {self.x_axis} dps, y-axis:
         {self.y_axis} dps, z-axis: {self.z_axis} dps"""

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "angular_velocity", {"x": self.x_axis, "y": self.y_axis, "z": self.z_axis, "magnitude": self.magnitude}


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


class CoordinatesDB(DataBlock):
    """Represents a coordinates data block"""

    def __init__(self, mission_time: int, latitude: int, longitude: int) -> None:
        """
        Constructs a coordinates data block.

        Args:
            mission_time: The mission time the coordinates were measured in milliseconds since launch.
            latitude: The latitude in units of degrees.
            longitude: The longitude in units of degrees.
        """
        super().__init__(mission_time)
        self.latitude: float = latitude
        self.longitude: float = longitude

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a coordinates data block from bytes.
        Returns:
            A coordinates data block.
        """
        parts = struct.unpack("<Iii", payload)
        return cls(parts[0], parts[1] / 1e7, parts[2] / 1e7)

    def __len__(self) -> int:
        """
        Get the length of a coordinates data block in bytes
        Returns:
            The length of a coordinates data block in bytes not including the block header.
        """
        return 12

    def __str__(self):
        return f"""{self.__class__.__name__} -> time: {self.mission_time} ms, latitude: {(self.latitude / pow(10, 7))}°
        , longitude: {(self.longitude / pow(10, 7))}°"""

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "latitude", self.latitude
        yield "longitude", self.longitude


class VoltageDB(DataBlock):
    """Represents a voltage data block"""

    def __init__(self, mission_time: int, id: int, voltage: int) -> None:
        """
        Constructus a voltage data block.

        Args:
            mission_time: The mission time the voltage was measured in milliseconds since launch.
            id: A numerical id associated with the voltage measurement for identification by the receiver
            voltage: The measured voltage in units of millivolts
        """
        super().__init__(mission_time)
        self.id: int = id
        self.voltage: int = voltage

    @classmethod
    def from_bytes(cls, payload: bytes) -> Self:
        """
        Constructs a voltage data block from bytes.
        Returns:
            A voltage data block.
        """
        parts = struct.unpack("<IHh", payload)
        return cls(parts[0], parts[1], parts[2])

    def __len__(self) -> int:
        """
        Get the length of a voltage data block in bytes
        Returns:
            The length of a voltage data block in bytes not including the block header.
        """
        return 8

    def __str__(self):
        return (
            f"""{self.__class__.__name__} -> time: {self.mission_time} ms, id: {self.id}, voltage: {self.voltage} mV"""
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "id", self.id
        yield "voltage", self.voltage
