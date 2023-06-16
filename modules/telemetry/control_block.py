# Defines the control block types
from abc import ABC, abstractmethod
from typing import Self
import logging
from modules.telemetry.block import ControlBlockSubtype, BlockException, BlockUnknownException

# Define logger
logger = logging.getLogger(__name__)


class ControlDataBlockException(BlockException):
    pass


class ControlBlockUnknownException(BlockUnknownException):
    pass


class ControlBlock(ABC):
    """Represents the base interface for a Control Block."""

    @abstractmethod
    def to_payload(self):
        """Marshal block to a bytes object"""

    @classmethod
    def parse_block(cls, block_subtype: ControlBlockSubtype, payload: bytes) -> Self:
        """Unmarshal a bytes object to appropriate block class"""
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
    """Represents a control block requesting signal report."""

    def __init__(self):  # TODO accept parameters for creating one of these
        super().__init__()
        self.mission_time: int = 0
        self.snr: int = 0
        self.tx_power: int = 0

    def __len__(self) -> int:
        return 16

    def to_payload(self) -> bytes:
        return bytes()  # TODO implement this method

    @classmethod
    def from_payload(cls, _: bytes) -> Self:
        return cls()

    def __str__(self):
        return f"{self.__class__.__name__} -> time: {self.mission_time}, snr: {self.snr}, power: {self.tx_power}"

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "snr", self.snr
        yield "power", self.tx_power
