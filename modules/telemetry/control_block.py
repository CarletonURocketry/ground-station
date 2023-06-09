from typing import Self, Generator
from abc import ABC, abstractmethod
from modules.telemetry.block import (
    ControlBlockSubtype,
    BlockException,
    BlockUnknownException,
)


class ControlDataBlockException(BlockException):
    pass


class ControlBlockUnknownException(BlockUnknownException):
    pass


class ControlBlock(ABC):
    """Defines the interface for control blocks."""

    def __init__(self, subtype: ControlBlockSubtype) -> None:
        self.subtype: ControlBlockSubtype = subtype

    @abstractmethod
    def to_payload(self) -> bytes:
        """Marshal block to a bytes object."""

    @classmethod
    def parse_block(cls, block_subtype: ControlBlockSubtype) -> Self:
        """Unmarshal a bytes object to appropriate block class."""
        match block_subtype:
            case _:
                raise NotImplementedError(
                    f"Block parsing is not yet implemented for ControlBlock of subtype {block_subtype}"
                )


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
    def from_payload(cls) -> Self:
        raise NotImplementedError()

    def __str__(self) -> str:
        return f"{self.__class__.__name__} -> time: {self.mission_time}, snr: {self.snr}, power: {self.tx_power}"

    def __iter__(self) -> Generator[tuple[str, int], None, None]:
        yield "mission_time", self.mission_time
        yield "snr", self.snr
        yield "power", self.tx_power
