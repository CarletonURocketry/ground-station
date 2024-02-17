# Contains universal block utilities for version 1 of the radio packet format
from dataclasses import dataclass
from enum import IntEnum
from typing import Self, Optional
import struct
import logging

from modules.telemetry.v1.data_block import DataBlockSubtype

# Set up logging
logger = logging.getLogger(__name__)


class BlockType(IntEnum):
    """The different radio block types for version 1 of the radio packet format."""

    DATA = 0x0
    RESERVED = 0xFF


class DeviceAddress(IntEnum):
    """Lists the different device addresses for version 1 of the radio packet format."""

    GROUND_STATION = 0x0
    ROCKET = 0x1
    RESERVED = 0xFE
    MULTICAST = 0xFF

    def __str__(self):
        match self:
            case DeviceAddress.GROUND_STATION:
                return "GROUND STATION"
            case DeviceAddress.ROCKET:
                return "ROCKET"
            case DeviceAddress.RESERVED:
                return "RESERVED"
            case DeviceAddress.MULTICAST:
                return "MULTICAST"


@dataclass
class PacketHeader:
    """Represents a V1 packet header."""

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
        ham_call_sign = amateur_radio[:6]
        ham_call_zone = amateur_radio[6:]
        if ham_call_sign.find("/") != -1:
            ham_call_sign = amateur_radio.split("/")[1]
            ham_call_zone = amateur_radio.split("/")[0]

        return cls(
            callsign=ham_call_sign.strip("/"),
            callzone=ham_call_zone.strip("/"),
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
    """Represents a V1 header for a telemetry block."""

    length: int
    message_type: int
    message_subtype: int
    destination: int
    valid: bool = True

    @classmethod
    def from_hex(cls, payload: str) -> Self:
        """
        Constructs a block header object from a hex payload.
        Returns:
            A newly constructed block header.
        """

        unpacked_header = struct.unpack("<BBBB", bytes.fromhex(payload))

        block_length = int(((unpacked_header[0]) + 1) * 4)
        block_type = int(unpacked_header[1])
        block_subtype = int(unpacked_header[2])
        block_destination = int(unpacked_header[3])
        block_valid = True

        try:
            _ = BlockType(block_type)
            _ = DataBlockSubtype(block_subtype)
            _ = DeviceAddress(block_destination)
        except ValueError:
            block_valid = False

        return cls(
            length=block_length,
            message_type=block_type,
            message_subtype=block_subtype,
            destination=block_destination,
            valid=block_valid,
        )

    def __len__(self) -> int:
        """
        Returns:
            The length of the block this header is associated with in bytes.
        """
        return self.length

    def __str__(self) -> str:
        """
        Returns a string representation of the block header
        """
        return (
            f"length {self.length}, type {self.message_type}, "
            f"subtype {self.message_subtype}, destination {self.destination}"
        )
