from abc import ABC, abstractmethod
from modules.telemetry.block import ControlBlockSubtype, BlockException, BlockUnknownException


class ControlDataBlockException(BlockException):
    pass


class ControlBlockUnknownException(BlockUnknownException):
    pass


class ControlBlock(ABC):

    @property
    @abstractmethod
    def length(self):
        """ Length of block """

    @property
    @abstractmethod
    def subtype(self):
        """ Subtype of block """

    @abstractmethod
    def to_payload(self):
        """ Marshal block to a bytes object """

    @staticmethod
    @abstractmethod
    def type_desc():
        """ String description of block type """

    @classmethod
    def parse_block(cls, block_subtype, payload):
        """ Unmarshal a bytes object to appropriate block class """
        match block_subtype:
            case ControlBlockSubtype.SIGNAL_REPORT:
                print("")
                return SignalReportControlBlock.from_payload(payload)
            case ControlBlockSubtype.COMMAND_ACKNOWLEDGEMENT:
                print("")
            case ControlBlockSubtype.COMMAND_NONCE_REQUEST:
                print("")
            case ControlBlockSubtype.COMMAND_NONCE:
                print("")
            case ControlBlockSubtype.BEACON:
                print("")
            case ControlBlockSubtype.BEACON_RESPONSE:
                print("")

        raise ControlBlockUnknownException(f"Unknown control block subtype: {block_subtype}")

    def __str__(self):
        return ""

    def __iter__(self):
        yield ""


class SignalReportControlBlock(ControlBlock):
    def __init__(self):
        self.mission_time = None
        self.snr = 0
        self.tx_power = 0

    @staticmethod
    def type_desc():
        return "Signal Report"

    def length(self):
        return 16

    def to_payload(self):
        return ""

    def subtype(self):
        return ""

    @classmethod
    def from_payload(cls, payload):
        return ""

    def __str__(self):
        return f"{self.type_desc()} -> time: {self.mission_time}, snr: {self.snr}, power: {self.tx_power}"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "snr", self.snr
        yield "power", self.tx_power
