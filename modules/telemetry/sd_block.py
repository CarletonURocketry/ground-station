import struct
from abc import ABC, abstractmethod
from enum import IntEnum

from modules.telemetry.data_block import DataBlock
from modules.telemetry.block import SDBlockClassType


class SDBlockException(Exception):
    pass


class SDBlockUnknownException(SDBlockException):
    pass


class SDBlock(ABC):
    @property
    @abstractmethod
    def block_class(self):
        """ Class of block """

    @property
    @abstractmethod
    def block_type(self):
        """ Class of block """

    @property
    @abstractmethod
    def length(self):
        """ Length of block """

    @staticmethod
    @abstractmethod
    def type_desc():
        """ String description of block type """

    def to_bytes(self):
        """ Marshal block to a bytes object """
        payload = self._payload_bytes()

        block_class_type = (self.block_class & 0x3f) | ((self.block_type & 0x3ff) << 6)
        head = struct.pack("<HH", block_class_type, len(self._payload_bytes) + 4)

        return head + payload

    @classmethod
    @abstractmethod
    def _parse(cls, block_type, length, payload):
        """ Unmarshal block from a bytes object (not meant to be called directly) """

    @abstractmethod
    def _payload_bytes(self):
        """ Marshal payload to bytes """

    @classmethod
    def from_bytes(cls, data):
        """ Unmarshal a bytes object to appropriate block class """
        if len(data) < 4:
            raise SDBlockException(f"Block must be at least 4 bytes long ({len(data)} bytes "
                                   f"read)")

        block_head = struct.unpack("<HH", data[0:4])
        try:
            block_class = SDBlockClassType(block_head[0] & 0x3f)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid block class: {block_head[0] & 0x3f:04x}") from error

        block_head = struct.unpack("<HH", data[0:4])
        block_type = block_head[0] >> 6
        block_length = block_head[1]

        if block_class == SDBlockClassType.LOGGING_METADATA:
            return LoggingMetadataBlock.from_payload(block_type, block_length, data[4:])
        if block_class == SDBlockClassType.TELEMETRY_DATA:
            # print(f"{data[0:4].hex(), block_type, block_length} \n")
            # print(data[0:4].hex(), block_type, block_length)
            # print(data[4:])
            return TelemetryDataBlock._parse(block_type, block_length, data[4:])
        if block_class == SDBlockClassType.DIAGNOSTIC_DATA:
            return DiagnosticDataBlock.from_payload(block_type, block_length, data[4:])

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

class LoggingMetadataBlockType(IntEnum):
    SPACER = 0x0


class LoggingMetadataBlock(SDBlock, ABC):
    @classmethod
    def from_payload(cls, block_type, length, payload):
        try:
            logging_meta_type = LoggingMetadataBlockType(block_type)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid logging metadata block type: {block_type:04x}") from error

        if logging_meta_type == LoggingMetadataBlockType.SPACER:
            return LoggingMetadataSpacerBlock._parse(logging_meta_type, length, payload)

        raise SDBlockUnknownException(f"Unknown logging metadata block type: {logging_meta_type}")


class LoggingMetadataSpacerBlock(LoggingMetadataBlock):
    def __init__(self, length):
        self.orig_length = length

    @property
    def block_class(self):
        return SDBlockClassType.LOGGING_METADATA

    @property
    def block_type(self):
        return LoggingMetadataBlockType.SPACER

    @property
    def length(self):
        return self.orig_length

    @staticmethod
    def type_desc():
        return "Logging Metadata -> Spacer"

    @classmethod
    def _parse(cls, block_type, length, payload):
        return LoggingMetadataSpacerBlock(length)

    def _payload_bytes(self):
        return b'\x00' * (self.length - 4)

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"


#
#   Telemetry Data
#

class TelemetryDataBlock(SDBlock):
    def __init__(self, data):
        self.data = data

    @property
    def block_class(self):
        return SDBlockClassType.TELEMETRY_DATA

    @property
    def block_type(self):
        return (self.data.block_type & 0xf) | ((self.data.subtype & 0x3f) << 4)

    @property
    def length(self):
        return 4 + self.data.length

    @staticmethod
    def type_desc():
        return f"Telemetry Data"

    @classmethod
    def _parse(cls, block_type, length, payload):
        data = DataBlock.parse(block_type, payload)
        # print(data.length,data.subtype,data)
        # print(data)
        # return TelemetryDataBlock(data), block_type, data.subtype, payload
        return TelemetryDataBlock(data)

    def _payload_bytes(self):
        return self.data.to_bytes()

    def __str__(self):
        return f"{self.type_desc()} -> {self.data}"


#
#   Diagnostic Data
#

class DiagnosticDataBlockType(IntEnum):
    LOG_MESSAGE = 0x0
    OUTGOING_RADIO_PACKET = 0x1
    INCOMING_RADIO_PACKET = 0x2


class DiagnosticDataBlock(SDBlock):
    @classmethod
    def from_payload(cls, block_type, length, payload):
        try:
            diag_data_type = DiagnosticDataBlockType(block_type)
        except ValueError as error:
            raise SDBlockUnknownException(f"Invalid diagnostic data block type: {block_type:04x}") from error

        if diag_data_type == DiagnosticDataBlockType.LOG_MESSAGE:
            return DiagnosticDataLogMessageBlock._parse(diag_data_type, length, payload)
        if diag_data_type == DiagnosticDataBlockType.OUTGOING_RADIO_PACKET:
            return DiagnosticDataOutgoingRadioPacketBlock._parse(diag_data_type, length, payload)
        if diag_data_type == DiagnosticDataBlockType.INCOMING_RADIO_PACKET:
            return DiagnosticDataIncomingRadioPacketBlock._parse(diag_data_type, length, payload)

        raise SDBlockUnknownException(f"Unknown diagnostic data block type: {diag_data_type}")


class DiagnosticDataLogMessageBlock(DiagnosticDataBlock):
    def __init__(self, mission_time, msg):
        self.mission_time = mission_time
        self.msg = msg

    @property
    def block_class(self):
        return SDBlockClassType.DIAGNOSTIC_DATA

    @property
    def block_type(self):
        return DiagnosticDataBlockType.LOG_MESSAGE

    @property
    def length(self):
        return 8 + ((len(self.msg.encode('utf-8')) + 3) & ~0x3)

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Message"

    @classmethod
    def _parse(cls, block_type, length, payload):
        mission_time = struct.unpack("<I", payload[0:4])[0]
        return DiagnosticDataLogMessageBlock(mission_time, payload[4:].decode('utf-8'))

    def _payload_bytes(self):
        b = self.msg.encode('utf-8')
        b = b + (b'\x00' * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f"{self.type_desc()} -> mission_time: {self.mission_time}, message: \"{self.msg}\""


class DiagnosticDataRadioPacketBlock(DiagnosticDataBlock):
    def __init__(self, mission_time, packet):
        self.mission_time = mission_time
        self.packet = packet

    @property
    def block_class(self):
        return SDBlockClassType.DIAGNOSTIC_DATA

    @property
    def length(self):
        return 4 + ((len(self.packet) + 3) & ~0x3)

    def _payload_bytes(self):
        p = self.packet
        p = p + (b'\x00' * (((len(p) + 3) & ~0x3) - len(p)))
        return p


class DiagnosticDataOutgoingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time, packet):
        super().__init__(mission_time, packet)

    @property
    def block_type(self):
        return DiagnosticDataBlockType.OUTGOING_RADIO_PACKET

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Outgoing Radio Packet"

    @classmethod
    def _parse(cls, block_type, length, payload):
        return DiagnosticDataOutgoingRadioPacketBlock(payload)

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"


class DiagnosticDataIncomingRadioPacketBlock(DiagnosticDataRadioPacketBlock):
    def __init__(self, mission_time, packet):
        super().__init__(mission_time, packet)

    @property
    def block_type(self):
        return DiagnosticDataBlockType.INCOMING_RADIO_PACKET

    @staticmethod
    def type_desc():
        return "Diagnostic Data -> Incoming Radio Packet"

    @classmethod
    def _parse(cls, block_type, length, payload):
        return DiagnosticDataIncomingRadioPacketBlock(payload)

    def __str__(self):
        return f"{self.type_desc()} -> length: {self.length}"
