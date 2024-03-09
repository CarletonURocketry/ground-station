# Generic block types and their subtypes
from dataclasses import dataclass
from enum import IntEnum
from typing import Self
import struct


class BlockException(Exception):
    """Base class for exceptions related to telemetry blocks"""
    pass


class BlockUnknownException(BlockException):
    """Exception raised when an unknown telemetry block subtype is encountered"""
    pass


class DeviceAddress(IntEnum):
    """
    Enumerates the possible device addresses from which packets can be sent.
    Attributes:
        - GROUND_STATION: Represents the device address for ground stations.
        - ROCKET: Represents the device address for rockets.
        - MULTICAST: Represents the device address for multicast transmissions.
    """

    GROUND_STATION = 0x0
    ROCKET = 0x1
    MULTICAST = 0xF

    def __str__(self):
        match self:
            case DeviceAddress.GROUND_STATION:
                return "GROUND STATION"
            case DeviceAddress.ROCKET:
                return "ROCKET"
            case DeviceAddress.MULTICAST:
                return "MULTICAST"


class RadioBlockType(IntEnum):
    """
    Enumeration class for different radio block classes.
    Attributes:
    - CONTROL: Control radio block class.
    - COMMAND: Command radio block class.
    - DATA: Data radio block class.
    - RESERVED: Reserved radio block class.
    """

    CONTROL = 0x0
    COMMAND = 0x1
    DATA = 0x2
    RESERVED = 0xF


class SDBlockSubtype(IntEnum):
    """
        Enumeration class for subtypes of SD Blocks.
        Attributes:
            - LOGGING_METADATA: Subtype for logging metadata blocks.
            - TELEMETRY_DATA: Subtype for telemetry data blocks.
            - DIAGNOSTIC_DATA: Subtype for diagnostic data blocks.
            - TELEMETRY_CONTROL: Subtype for telemetry control blocks.
            - TELEMETRY_COMMAND: Subtype for telemetry command blocks.
            - RESERVED: Reserved subtype."""

    LOGGING_METADATA = 0x0
    TELEMETRY_DATA = 0x1
    DIAGNOSTIC_DATA = 0x2
    TELEMETRY_CONTROL = 0x3
    TELEMETRY_COMMAND = 0x4
    RESERVED = 0x3F


class ControlBlockSubtype(IntEnum):
    """
    Enumeration class for subtypes of telemetry command blocks.
    Attributes:
        - SIGNAL_REPORT: Subtype for signal report command blocks.
        - COMMAND_ACKNOWLEDGEMENT: Subtype for command acknowledgement command blocks.
        - COMMAND_NONCE_REQUEST: Subtype for command nonce request command blocks.
        - COMMAND_NONCE: Subtype for command nonce command blocks.
        - BEACON: Subtype for beacon command blocks.
        - BEACON_RESPONSE: Subtype for beacon response command blocks.
        - RESERVED: Reserved subtype."""
    SIGNAL_REPORT = 0x00
    COMMAND_ACKNOWLEDGEMENT = 0x01
    COMMAND_NONCE_REQUEST = 0x02
    COMMAND_NONCE = 0x03
    BEACON = 0x04
    BEACON_RESPONSE = 0x05
    RESERVED = 0x3F


class CommandBlockSubtype(IntEnum):
    """
    Enumeration class for subtypes of telemetry control blocks.
    Attributes:
        - RESET_ROCKET_AVIONICS: Subtype for resetting rocket avionics control blocks.
        - REQUEST_TELEMETRY_DATA: Subtype for requesting telemetry data control blocks.
        - DEPLOY_PARACHUTE: Subtype for deploying parachute control blocks.
        - TARE_SENSORS: Subtype for taring sensors control blocks.
        - RESERVED: Reserved subtype."""

    RESET_ROCKET_AVIONICS = 0x00
    REQUEST_TELEMETRY_DATA = 0x01
    DEPLOY_PARACHUTE = 0x02
    TARE_SENSORS = 0x03
    RESERVED = 0x3F


class DataBlockSubtype(IntEnum):
    """
        Enumeration class for subtypes of telemetry data blocks.
        Attributes:
            - DEBUG_MESSAGE: Subtype for debug message data blocks.
            - STATUS: Subtype for status data blocks.
            - STARTUP_MESSAGE: Subtype for startup message data blocks.
            - ALTITUDE: Subtype for altitude data blocks.
            - ACCELERATION: Subtype for acceleration data blocks.
            - ANGULAR_VELOCITY: Subtype for angular velocity data blocks.
            - GNSS: Subtype for GNSS data blocks.
            - GNSS_META: Subtype for GNSS meta data blocks.
            - POWER: Subtype for power data blocks.
            - TEMPERATURE: Subtype for temperature data blocks.
            - MPU9250_IMU: Subtype for MPU9250 IMU data blocks.
            - KX134_1211_ACCEL: Subtype for KX134-1211 accelerometer data blocks.
            - RESERVED: Reserved subtype."""

    DEBUG_MESSAGE = 0x00
    STATUS = 0x01
    STARTUP_MESSAGE = 0x02
    ALTITUDE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS = 0x06
    GNSS_META = 0x07
    POWER = 0x08
    TEMPERATURE = 0x09
    MPU9250_IMU = 0x0A
    KX134_1211_ACCEL = 0x0B
    RESERVED = 0x3F


class LoggingMetadataBlockSubtype(IntEnum):
    """
    Enumeration class for subtypes of logging metadata blocks.
    Attributes:
        - SPACER: Subtype for spacer logging metadata blocks.
        """

    SPACER = 0x0


class DiagnosticDataBlockSubtype(IntEnum):
    """Enumeration class for subtypes of diagnostic data blocks.
    Attributes:
        - LOG_MESSAGE: Subtype for log message diagnostic data blocks.
        - OUTGOING_RADIO_PACKET: Subtype for outgoing radio packet diagnostic data blocks.
        - INCOMING_RADIO_PACKET: Subtype for incoming radio packet diagnostic data blocks."""

    LOG_MESSAGE = 0x0
    OUTGOING_RADIO_PACKET = 0x1
    INCOMING_RADIO_PACKET = 0x2


@dataclass
class BlockHeader:
    """Represents a header for a telemetry block."""

    length: int
    has_crypto: bool  # Has a cryptographic signature
    message_type: int
    message_subtype: int
    destination: int

    @classmethod
    def from_hex(cls, payload: str) -> Self:
        """
        Constructs a block header object from a hex payload.
        Returns:
            A newly constructed block header.
        """
        unpacked_header: int = struct.unpack("<I", bytes.fromhex(payload))[0]
        return cls(
            length=((unpacked_header & 0x1F) + 1) * 4,
            has_crypto=bool((unpacked_header >> 5) & 0x1),
            message_type=(unpacked_header >> 6) & 0xF,
            message_subtype=(unpacked_header >> 10) & 0x3F,
            destination=(unpacked_header >> 16) & 0xF,
        )

    def __len__(self) -> int:
        """
        Returns:
            The length of the block this header is associated with in bytes.
        """
        return self.length
