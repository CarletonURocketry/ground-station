# Contains the implementation for SD card blocks
# Matteo Golin

# Imports
import struct
from abc import ABC, abstractmethod

from modules.telemetry.data_block import DataBlock
import modules.telemetry.block as blk


# Custom Exceptions
class SDBlockException(blk.BlockException):
    pass


class SDBlockUnknownException(blk.BlockUnknownException):
    pass


class SDBlock(ABC):
    @property
    @abstractmethod
    def block_class(self):
        """ Class of block (Logging metadata, telemetry data, diagnostic data, ...)"""

    @property
    @abstractmethod
    def block_subtype(self):
        """ Subtype of block (Altitude, GNSS, GNSS Meta, IMU, ...)"""

    @property
    @abstractmethod
    def length(self):
        """ Length of block in bytes """

    @staticmethod
    @abstractmethod
    def type_desc():
        """ String description of block type """

    def to_bytes(self):
        """ Marshal block to a bytes object """
        payload = self._payload_bytes()

        block_class_type = (int(self.block_class) & 0x3f) | ((int(self.block_subtype) & 0x3ff) << 6)
        head = struct.pack("<HH", block_class_type, self.length)

        return head + payload

    @classmethod
    @abstractmethod
    def from_payload(cls, block_type, length, payload):
        """ Unmarshal block from a bytes object (not meant to be called directly) """

    @abstractmethod
    def _payload_bytes(self):
        """ Marshal payload to bytes """

    @classmethod
    def from_bytes(cls, data):
        """ Unmarshal a bytes object to appropriate block class """
        if len(data) < 4:
            raise SDBlockException(f"Block must be at least 4 bytes long ({len(data)} bytes read)")

        block_head = struct.unpack("<HH", data[0:4])
        try:
            block_class = blk.SDBlockClassType(block_head[0] & 0x3f)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid block class: {block_head[0] & 0x3f:04x}") from error

        block_subtype = block_head[0] >> 6
        block_length = block_head[1]
        match block_class:
            case blk.SDBlockClassType.LOGGING_METADATA:
                return LoggingMetadataBlock.from_payload(block_subtype, block_length, data[4:])
            case blk.SDBlockClassType.TELEMETRY_DATA:
                return TelemetryDataBlock.from_payload(block_subtype, block_length, data[4:])
            case blk.SDBlockClassType.DIAGNOSTIC_DATA:
                return DiagnosticDataBlock.from_payload(block_subtype, block_length, data[4:])

        raise SDBlockUnknownException(f"Unknown block class: {block_class}")

    @classmethod
    def parse_length(cls, data):
        """ Helper to get block length without parsing the whole block, good for invalid blocks """

        if len(data) < 4:
            raise SDBlockException(f"Block must be at least 4 bytes long ({len(data)} bytes "
                                   f"read)")

        return struct.unpack("<H", data[2:4])[0]


#
#   Logging Metadata
#


class LoggingMetadataBlock(SDBlock, ABC):
    @property
    def block_class(self) -> blk.SDBlockClassType:
        return blk.SDBlockClassType.LOGGING_METADATA

    @classmethod
    def from_payload(cls, block_subtype, length, payload):
        try:
            logging_meta_type = blk.LoggingMetadataBlockSubtype(block_subtype)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid logging metadata block subtype: {block_subtype:04x}") from error

        if logging_meta_type == blk.LoggingMetadataBlockSubtype.SPACER:
            return LoggingMetadataSpacerBlock.from_payload(logging_meta_type, length, payload)

        raise SDBlockUnknownException(f"Unknown logging metadata block type: {logging_meta_type}")


class LoggingMetadataSpacerBlock(LoggingMetadataBlock):
    def __init__(self, length):
        self.length_with_header = length
        self.length_without_header = length - 4

    @property
    def block_subtype(self) -> blk.LoggingMetadataBlockSubtype:
        return blk.LoggingMetadataBlockSubtype.SPACER

    @property
    def length(self) -> int:
        return self.length_with_header

    @staticmethod
    def type_desc() -> str:
        return "Logging Metadata -> Spacer"

    @classmethod
    def from_payload(cls, block_type, length, payload):
        return LoggingMetadataSpacerBlock(length)

    def _payload_bytes(self) -> bytes:
        return b'\x00' * self.length_without_header

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"


#
#   Telemetry Data
#

class TelemetryDataBlock(SDBlock):
    def __init__(self, data):
        self.data = data

    @property
    def block_class(self) -> blk.SDBlockClassType:
        return blk.SDBlockClassType.TELEMETRY_DATA

    @property
    def block_subtype(self) -> blk.DataBlockSubtype:
        return self.data.subtype

    @property
    def length(self) -> int:
        """ 
        Length of the telemetry data in bytes 
        
        Four bytes for the block header, then the block contents itself.
        """
        return 4 + self.data.length

    @staticmethod
    def type_desc():
        return f"Telemetry Data"

    @classmethod
    def from_payload(cls, block_subtype, length, payload):
        return TelemetryDataBlock(DataBlock.parse(block_subtype, payload))

    def _payload_bytes(self) -> bytes:
        return self.data.to_payload()

    def __str__(self):
        return f"{self.type_desc()} -> {self.data}"


#
#   Diagnostic Data
#

class DiagnosticDataBlock(SDBlock):
    @classmethod
    def from_payload(cls, block_type, length, payload):
        try:
            diag_data_type = blk.DiagnosticDataBlockSubtype(block_type)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid diagnostic data block type: {block_type:04x}") from error

        if diag_data_type == blk.DiagnosticDataBlockSubtype.LOG_MESSAGE:
            return DiagnosticDataLogMessageBlock.from_payload(diag_data_type, length, payload)
        if diag_data_type == blk.DiagnosticDataBlockSubtype.OUTGOING_RADIO_PACKET:
            return DiagnosticDataOutgoingRadioPacketBlock.from_payload(diag_data_type, length, payload)
        if diag_data_type == blk.DiagnosticDataBlockSubtype.INCOMING_RADIO_PACKET:
            return DiagnosticDataIncomingRadioPacketBlock.from_payload(diag_data_type, length, payload)

        raise SDBlockUnknownException(f"Unknown diagnostic data block type: {diag_data_type}")


class DiagnosticDataRadioPacketBlock(DiagnosticDataBlock):
    def __init__(self, mission_time, packet):
        self.mission_time = mission_time
        self.packet = packet

    @property
    def block_class(self):
        return blk.SDBlockClassType.DIAGNOSTIC_DATA

    @property
    def length(self):
        return 4 + ((len(self.packet) + 3) & ~0x3)

    def _payload_bytes(self):
        p = self.packet
        p = p + (b'\x00' * (((len(p) + 3) & ~0x3) - len(p)))
        return p


class DiagnosticDataLogMessageBlock(DiagnosticDataBlock):
    def __init__(self, mission_time, msg):
        self.mission_time = mission_time
        self.msg = msg

    @property
    def block_class(self):
        return blk.SDBlockClassType.DIAGNOSTIC_DATA

    @property
    def block_type(self):
        return blk.DiagnosticDataBlockSubtype.LOG_MESSAGE

    @property
    def length(self):
        return 8 + ((len(self.msg.encode('utf-8')) + 3) & ~0x3)

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Message"

    @classmethod
    def from_payload(cls, block_type, length, payload):
        mission_time = struct.unpack("<I", payload[0:4])[0]
        return cls(mission_time, payload[4:].decode('utf-8'))

    def _payload_bytes(self):
        b = self.msg.encode('utf-8')
        b = b + (b'\x00' * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f"{self.type_desc()} -> time: {self.mission_time}, message: \"{self.msg}\""


class DiagnosticDataOutgoingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time, packet):
        super().__init__(mission_time, packet)

    @property
    def subtype(self):
        return blk.DiagnosticDataBlockSubtype.OUTGOING_RADIO_PACKET

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Outgoing Radio Packet"

    @classmethod
    def from_payload(cls, block_type, length, payload):
        return DiagnosticDataOutgoingRadioPacketBlock(payload)

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"


class DiagnosticDataIncomingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time, packet):
        super().__init__(mission_time, packet)

    @property
    def subtype(self):
        return blk.DiagnosticDataBlockSubtype.INCOMING_RADIO_PACKET

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Incoming Radio Packet"

    @classmethod
    def from_payload(cls, block_type, length, payload):
        return DiagnosticDataIncomingRadioPacketBlock(payload)

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"
