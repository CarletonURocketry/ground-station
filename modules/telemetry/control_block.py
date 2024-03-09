# Defines the control block types
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Generator
import logging
from modules.telemetry.block import ControlBlockSubtype, BlockException, BlockUnknownException

# Define logger
logger = logging.getLogger(__name__)


class ControlDataBlockException(BlockException):
    """
       Exception raised for errors related to control data blocks.
    """
    pass


class ControlBlockUnknownException(BlockUnknownException):
    """
        Exception raised when an unknown control block subtype is encountered.
    """
    pass


class ControlBlock(ABC):
    """Abstract base class defining the interface for control blocks.
    Attributes:
        subtype (ControlBlockSubtype): The subtype of the control block."""

    def __init__(self, subtype: ControlBlockSubtype) -> None:
        """
                Initialize a ControlBlock instance.
                Args:
                    subtype (ControlBlockSubtype): The subtype of the control block.
        """
        super().__init__()
        self.subtype: ControlBlockSubtype = subtype

    @abstractmethod
    def to_payload(self) -> bytes:
        """Marshal the control block to a bytes object.
        Returns:
            bytes: The marshaled control block.
        ."""

    @classmethod
    def parse_block(cls, block_subtype: ControlBlockSubtype, payload: bytes) -> ControlBlock:
        """Unmarshal a bytes object to an appropriate block class.
        Args:
            block_subtype (ControlBlockSubtype): The subtype of the control block.
            payload (bytes): The payload containing the control block data.
        Returns:
            ControlBlock: The parsed control block instance.
        Raises:
            ControlBlockUnknownException: If the block subtype is unknown.
        ."""
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
    """
    Represents a control block requesting a signal report.
    Attributes:
        mission_time (int): The mission time.
        snr (int): The signal-to-noise ratio.
        tx_power (int): The transmission power.
    """

    def __init__(self):
        super().__init__(ControlBlockSubtype.SIGNAL_REPORT)
        self.mission_time: int = 0
        self.snr: int = 0
        self.tx_power: int = 0

    def __len__(self) -> int:
        """
                Get the length of the control block.
                Returns:
                    int: The length of the control block
        """
        return 16

    def to_payload(self) -> bytes:
        """
        Marshal the control block to a bytes object.
            bytes: The marshaled control block.
        """
        raise NotImplementedError()

    @classmethod
    def from_payload(cls, _: bytes) -> Self:
        """
               Construct a SignalReportControlBlock instance from a payload.
               Args:
                   _: The payload containing the control block data.
               Returns:
                   SignalReportControlBlock: The constructed control block instance.
               """
        return cls()

    def __str__(self) -> str:
        """
               Get a string representation of the control block.
               Returns:
                   str: A string representation of the control block.
               """
        return f"{self.__class__.__name__} -> time: {self.mission_time}, snr: {self.snr}, power: {self.tx_power}"

    def __iter__(self) -> Generator[tuple[str, int], None, None]:
        """
                Iterate over the attributes of the control block.
                Yields:
                    tuple[str, int]: A tuple containing the attribute name and value.
                """
        yield "mission_time", self.mission_time
        yield "snr", self.snr
        yield "power", self.tx_power
