# Defines the control block types
from abc import ABC, abstractmethod
from typing import Self, Generator
import logging
from modules.telemetry.block import ControlBlockSubtype, BlockException, BlockUnknownException

# Define logger
logger = logging.getLogger(__name__)


class ControlDataBlockException(BlockException):
    pass


class ControlBlockUnknownException(BlockUnknownException):
    pass


class ControlBlock(ABC):
    """Defines the interface for control blocks."""

    def __init__(self, subtype: ControlBlockSubtype) -> None:
        super().__init__()
        self.subtype: ControlBlockSubtype = subtype

    @abstractmethod
    def to_payload(self) -> bytes:
        """Marshal block to a bytes object."""

    @classmethod
    def parse_block(cls, block_subtype: ControlBlockSubtype, payload: bytes) -> Self:
        """Unmarshal a bytes object to appropriate block class."""
        match block_subtype:
            case ControlBlockSubtype.SIGNAL_REPORT:
                logger.debug("Control block of type {block_subtype} received.")
                return SignalReportControlBlock.from_payload(payload)
            case ControlBlockSubtype.COMMAND_ACKNOWLEDGEMENT:
                logger.debug("Control block of type {block_subtype} received.")
            case ControlBlockSubtype.COMMAND_NONCE_REQUEST:
                logger.debug("Control block of type {block_subtype} received.")
            case ControlBlockSubtype.COMMAND_NONCE:
                logger.debug("Control block of type {block_subtype} received.")
            case ControlBlockSubtype.BEACON:
                logger.debug("Control block of type {block_subtype} received.")
            case ControlBlockSubtype.BEACON_RESPONSE:
                logger.debug("Control block of type {block_subtype} received.")
            case ControlBlockSubtype.RESERVED:
                logger.debug("Control block of type {block_subtype} received.")

        raise ControlBlockUnknownException(f"Unknown control block subtype: {block_subtype}")


class SignalReportControlBlock(ControlBlock):
    """Represents a control block requesting a signal report."""

    def __init__(self):
        super().__init__(ControlBlockSubtype.SIGNAL_REPORT)
        self.mission_time: int = 0
        self.snr: int = 0
        self.tx_power: int = 0

    def __len__(self) -> int:
        return 16

    def to_payload(self) -> bytes:
        raise NotImplementedError()

    @classmethod
    def from_payload(cls, _: bytes) -> Self:
        return cls()

    def __str__(self) -> str:
        return f"{self.__class__.__name__} -> time: {self.mission_time}, snr: {self.snr}, power: {self.tx_power}"

    def __iter__(self) -> Generator[tuple[str, int], None, None]:
        yield "mission_time", self.mission_time
        yield "snr", self.snr
        yield "power", self.tx_power
