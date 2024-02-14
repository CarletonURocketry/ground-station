# Generic block types and their subtypes
from dataclasses import dataclass
from enum import IntEnum
from typing import Self, Optional
import struct


class BlockException(Exception):
    pass


class BlockUnknownException(BlockException):
    pass


class DeviceAddress(IntEnum):
    """Lists the different device addresses packets can be sent from."""

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
    """Lists the different radio block classes."""

    CONTROL = 0x0
    COMMAND = 0x1
    DATA = 0x2
    RESERVED = 0xF


class SDBlockSubtype(IntEnum):
    """Lists the different SD Block classes."""

    LOGGING_METADATA = 0x0
    TELEMETRY_DATA = 0x1
    DIAGNOSTIC_DATA = 0x2
    TELEMETRY_CONTROL = 0x3
    TELEMETRY_COMMAND = 0x4
    RESERVED = 0x3F


class ControlBlockSubtype(IntEnum):
    """Lists the subtypes of telemetry command blocks."""

    SIGNAL_REPORT = 0x00
    COMMAND_ACKNOWLEDGEMENT = 0x01
    COMMAND_NONCE_REQUEST = 0x02
    COMMAND_NONCE = 0x03
    BEACON = 0x04
    BEACON_RESPONSE = 0x05
    RESERVED = 0x3F


class CommandBlockSubtype(IntEnum):
    """Lists the subtypes of telemetry control blocks."""

    RESET_ROCKET_AVIONICS = 0x00
    REQUEST_TELEMETRY_DATA = 0x01
    DEPLOY_PARACHUTE = 0x02
    TARE_SENSORS = 0x03
    RESERVED = 0x3F


class DataBlockSubtype(IntEnum):
    """Lists the subtypes of telemetry data blocks."""

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
    """Lists the subtypes of logging meta blocks."""

    SPACER = 0x0


class DiagnosticDataBlockSubtype(IntEnum):
    """Lists the subtypes of diagnostic blocks."""

    LOG_MESSAGE = 0x0
    OUTGOING_RADIO_PACKET = 0x1
    INCOMING_RADIO_PACKET = 0x2


@dataclass
class PacketHeader:
    """Represents a packet header."""

    callsign: str
    callzone: Optional[str]
    length: int
    version: int
    src_addr: int
    packet_num: int

    @classmethod
    def from_hex(cls, payload: str) -> Self:
        """
        Constructs a new packet header from a hex payload.
        Returns:
            A newly constructed packet header object.
        """
        header = bin(int(payload, 16))[2:]

        # Decodes the call sign/call zone from packet header
        # Rearranges if call zone (W5/VE3LWN) is first
        amateur_radio = bytes.fromhex(payload[:18]).decode("utf-8").strip("\x00").upper()
        ham_callsign = amateur_radio[:6]
        ham_callzone = amateur_radio[6:]
        if ham_callsign.find("/") != -1:
            ham_callsign = amateur_radio.split("/")[1]
            ham_callzone = amateur_radio.split("/")[0]

        return cls(
            callsign=ham_callsign.strip("/"),
            callzone=ham_callzone.strip("/"),
            length=(int(header[71:79], 2) + 1) * 4,
            version=int(header[79:87], 2),
            src_addr=int(header[87:95], 2),
            packet_num=struct.unpack(">I", struct.pack("<I", int(header[95:127], 2)))[0],
        )

    def __len__(self) -> int:
        """
        Returns:
            The length of the packet associated with this packet header in bytes.
        """
        return self.length


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
