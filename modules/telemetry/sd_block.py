# Contains the implementation for SD card blocks
# Matteo Golin

# Imports
from __future__ import annotations
import struct
from abc import ABC, abstractmethod
from typing import Self, Any
from modules.telemetry.data_block import DataBlock
import modules.telemetry.block as blk


# Custom Exceptions
class SDBlockException(blk.BlockException):
    """SDBLock module exception."""

    pass


class SDBlockUnknownException(blk.BlockUnknownException):
    """Unknown exception from SDBlock module."""

    pass


class SDBlock(ABC):
    """Defines the interface for all SDBlock subtypes."""

    def __init__(self, sd_subtype: blk.SDBlockSubtype, subtype: Any) -> None:
        super().__init__()
        self.sd_subtype: blk.SDBlockSubtype = sd_subtype
        self.subtype: Any = subtype

    def __len__(self) -> int:
        """Length of the block in bytes."""
        return 0

    def to_bytes(self):
        """Marshal block to a bytes object"""
        payload = self._payload_bytes()

        block_class_type = (int(self.sd_subtype) & 0x3F) | ((int(self.subtype) & 0x3FF) << 6)
        head = struct.pack("<HH", block_class_type, len(self))

        return head + payload

    @abstractmethod
    def _payload_bytes(self) -> bytes:
        """Marshal payload to bytes"""

    @classmethod
    def from_bytes(cls, byte_data: bytes) -> Self:
        """Unmarshal a bytes object to appropriate block class."""
        if len(byte_data) < 4:
            raise SDBlockException(f"Block must be at least 4 bytes long ({len(byte_data)} bytes read)")

        block_head = struct.unpack("<HH", byte_data[0:4])
        block_subtype = block_head[0] >> 6
        block_length = block_head[1]
        block_sd_subtype = blk.SDBlockSubtype(block_head[0] & 0x3F)

        match block_sd_subtype:
            case blk.SDBlockSubtype.LOGGING_METADATA:
                return LoggingMetadataBlock.from_payload(block_subtype, block_length)
            case blk.SDBlockSubtype.TELEMETRY_DATA:
                return TelemetryDataBlock.from_payload(block_subtype, byte_data[4:])
            case blk.SDBlockSubtype.DIAGNOSTIC_DATA:
                return DiagnosticDataBlock.from_payload(block_subtype, byte_data[4:])
            case _:
                raise NotImplementedError(f"from_bytes method not implemented for type {block_sd_subtype}.")

    @classmethod
    def parse_length(cls, data: bytes):
        """Helper to get block length without parsing the whole block, good for invalid blocks."""

        if len(data) < 4:
            raise SDBlockException(f"Block must be at least 4 bytes long ({len(data)} bytes read).")

        return struct.unpack("<H", data[2:4])[0]


# Logging Metadata
class LoggingMetadataBlock(SDBlock):
    """Responsible for tracking how to initialize logging metadata blocks."""

    def __init__(self, subtype: blk.LoggingMetadataBlockSubtype) -> None:
        super().__init__(blk.SDBlockSubtype.LOGGING_METADATA, subtype)

    @staticmethod
    def from_payload(block_subtype: int, length: int) -> LoggingMetadataBlock:
        subtype = blk.LoggingMetadataBlockSubtype(block_subtype)  # Throws error with invalid block type

        match subtype:
            case blk.LoggingMetadataBlockSubtype.SPACER:
                return LoggingMetadataSpacerBlock(length)


class LoggingMetadataSpacerBlock(LoggingMetadataBlock):
    """Represents a logging metadata spacer block."""

    def __init__(self, length: int):
        super().__init__(blk.LoggingMetadataBlockSubtype.SPACER)
        self.length_with_header: int = length

    def __len__(self) -> int:
        return self.length_with_header

    @property
    def len_without_header(self) -> int:
        """The length of the spacer block not including the header."""
        return len(self) - 4

    def _payload_bytes(self) -> bytes:
        return b"\x00" * self.len_without_header

    def __str__(self):
        return f"{self.__class__.__name__} -> length: {len(self)}"


# Telemetry Data
class TelemetryDataBlock(SDBlock):
    """Responsible for initializing data blocks."""

    def __init__(self, subtype: blk.DataBlockSubtype, data: DataBlock):
        super().__init__(blk.SDBlockSubtype.TELEMETRY_DATA, subtype)
        self.data = data

    def __len__(self) -> int:
        """Length of the telemetry data in bytes. Four bytes for the block header, then the block contents itself."""
        return 4 + len(self.data)

    @classmethod
    def from_payload(cls, block_subtype: int, payload: bytes) -> Self:
        subtype = blk.DataBlockSubtype(block_subtype)
        return cls(subtype, DataBlock.parse(subtype, payload))

    def _payload_bytes(self) -> bytes:
        return self.data.to_payload()

    def __str__(self):
        return f"{self.__class__.__name__} -> {self.data}"


#   Diagnostic Data
class DiagnosticDataBlock(SDBlock):
    def __init__(self, subtype: blk.DiagnosticDataBlockSubtype) -> None:
        super().__init__(blk.SDBlockSubtype.DIAGNOSTIC_DATA, subtype)

    @classmethod
    def from_payload(cls, block_type: blk.DiagnosticDataBlockSubtype, payload: bytes) -> Self:
        """Returns a DiagnosticDataBlock subclass populated with the payload."""
        diagnostic_subtype = blk.DiagnosticDataBlockSubtype(block_type)

        match diagnostic_subtype:
            case blk.DiagnosticDataBlockSubtype.LOG_MESSAGE:
                return DiagnosticDataLogMessageBlock.from_payload(payload)
            case blk.DiagnosticDataBlockSubtype.OUTGOING_RADIO_PACKET:
                return DiagnosticDataOutgoingRadioPacketBlock.from_payload(payload)
            case blk.DiagnosticDataBlockSubtype.INCOMING_RADIO_PACKET:
                return DiagnosticDataIncomingRadioPacketBlock.from_payload(payload)


class DiagnosticDataRadioPacketBlock(DiagnosticDataBlock):
    def __init__(self, subtype: blk.DiagnosticDataBlockSubtype, mission_time: int, packet: bytes):
        super().__init__(subtype)
        self.mission_time: int = mission_time
        self.packet = packet

    def __len__(self):
        return 4 + ((len(self.packet) + 3) & ~0x3)

    def _payload_bytes(self):
        p = self.packet
        p = p + (b"\x00" * (((len(p) + 3) & ~0x3) - len(p)))
        return p


class DiagnosticDataLogMessageBlock(DiagnosticDataBlock):
    def __init__(self, mission_time: int, msg: str):
        super().__init__(blk.DiagnosticDataBlockSubtype.LOG_MESSAGE)
        self.mission_time: int = mission_time
        self.msg: str = msg

    def __len__(self):
        return 8 + ((len(self.msg.encode("utf-8")) + 3) & ~0x3)

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        mission_time = struct.unpack("<I", payload[:4])[0]
        return cls(mission_time, payload[4:].decode("utf-8"))

    def _payload_bytes(self):
        b = self.msg.encode("utf-8")
        b = b + (b"\x00" * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f'{self.__class__.__name__} -> time: {self.mission_time}, message: "{self.msg}"'


class DiagnosticDataOutgoingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time: int, packet: bytes):
        super().__init__(blk.DiagnosticDataBlockSubtype.OUTGOING_RADIO_PACKET, mission_time, packet)

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        mission_time = struct.unpack("<I", payload[:4])[0]
        return cls(mission_time, payload)

    def __str__(self):
        return f"{self.__class__.__name__} -> length: {len(self)}"


class DiagnosticDataIncomingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time: int, packet: bytes):
        super().__init__(blk.DiagnosticDataBlockSubtype.INCOMING_RADIO_PACKET, mission_time, packet)

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        mission_time = struct.unpack("<I", payload[:4])[0]
        return cls(mission_time, payload)

    def __str__(self):
        return f"{self.__class__.__name__} -> length: {len(self)}"
