# Contains the logic for unpacking user configuration file
__author__ = "Matteo Golin"

# Imports
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Self

# Constants (note that trailing +1 is for inclusivity in range() object)
POWER_RANGE: tuple[int, int] = (-3, 16 + 1)
VALID_SPREADING_FACTORS: list[int] = [7, 8, 9, 10, 11, 12]
VALID_BANDWIDTHS: list[int] = [125, 250, 500]
SYNC_RANGE: tuple[int, int] = (0, 256 + 1)
PREAMBLE_RANGE: tuple[int, int] = (0, 65_535 + 1)
LF_RANGE: tuple[int, int] = (433_050_000, 434_790_000 + 1)
HF_RANGE: tuple[int, int] = (863_000_000, 870_000_000 + 1)

# Types
JSON = dict[str, Any]


class ModulationModes(StrEnum):
    """Modulation types for the RN2483 radio."""

    LORA = "lora"
    FSK = "fsk"


class CodingRates(StrEnum):
    """Coding rates for the RN2483 radio."""

    FOUR_FIFTHS = "4/5"
    FOUR_SIXTHS = "4/6"
    FOUR_SEVENTHS = "4/7"
    FOUR_EIGHTS = "4/8"


@dataclass
class RadioParameters:

    """
    Represents a collection of parameters for the RN2483 radio settings.

    modulation: The modulation type.
    frequency: The frequency in Hz.
    power: The 15th state has an output power of 14.1dBm for 868MHz and 13.6dBm for 433MHz.
    spread_factor: Higher spreading factor means slower transmissions, but system will have better reception and less
    error.
    coding_rate: The ratio of actual data to error-correcting data.
    bandwidth: The bandwidth allocated to the transmission.
    preamble_len: The length of the transmission used to synchronize the receiver.
    cyclic_redundancy: Enable or disable cyclic redudancy check used to detect errors in the received signal.
    iqi: Invert IQ function enabled/disabled.
    sync_word: The radio sync word.
    """

    modulation: ModulationModes = ModulationModes.LORA
    frequency: int = 433_050_000
    power: int = 15
    spread_factor: int = 9
    coding_rate: CodingRates = CodingRates.FOUR_SEVENTHS
    bandwidth: int = 500
    preamble_len: int = 6
    cyclic_redundancy: bool = True
    iqi: bool = False
    sync_word: str = "0x43"

    def __post_init__(self):
        if self.frequency not in range(*LF_RANGE) and self.frequency not in range(*HF_RANGE):
            raise ValueError(
                f"Frequency '{self.frequency}' not in low frequency range {LF_RANGE} or high frequency range {HF_RANGE}"
            )

        if self.power not in range(*POWER_RANGE):
            raise ValueError(f"Power '{self.power}' not within allowed range {POWER_RANGE}")

        if self.spread_factor not in VALID_SPREADING_FACTORS:
            raise ValueError(f"Spread factor '{self.spread_factor}' invalid; must be one of {VALID_SPREADING_FACTORS}")

        if self.preamble_len not in range(*PREAMBLE_RANGE):
            raise ValueError(f"Preamble length '{self.preamble_len}' not within allowed range of {PREAMBLE_RANGE}")

        if int(self.sync_word, 16) not in range(*SYNC_RANGE):
            raise ValueError(f"Sync word '{self.sync_word}' not within allowed range of {SYNC_RANGE}")
        self.sync_word = self.sync_word[2:]  # Remove 0x

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Builds a new RadioParameters object from JSON data found in a config file."""

        # Radio parameters are either initialized with an explicitly defined value from the config file, or
        # are assigned a default value.
        return cls(
            modulation=ModulationModes(data.get("modulation", "lora")),
            frequency=data.get("frequency", 433_050_000),
            power=data.get("power", 15),
            spread_factor=data.get("spread_factor", 9),
            coding_rate=CodingRates(data.get("coding_rate", "4/7")),
            bandwidth=data.get("bandwidth", 500),
            preamble_len=data.get("preamble_len", 6),
            cyclic_redundancy=data.get("cyclic_redundancy", True),
            iqi=data.get("iqi", False),
            sync_word=data.get("sync_word", "0x43"),
        )

    def __iter__(self):
        yield "modulation", self.modulation.value
        yield "frequency", self.frequency
        yield "power", self.power
        yield "spread_factor", self.spread_factor
        yield "coding_rate", self.coding_rate.value
        yield "bandwidth", self.bandwidth
        yield "preamble_len", self.preamble_len
        yield "cyclic_redundancy", self.cyclic_redundancy
        yield "iqi", self.iqi
        yield "sync_word", self.sync_word


@dataclass
class Config:

    """Contains the configuration for the ground station process."""

    organization: str = "CUInSpace"
    rocket_name: str = "Red Ballistic"
    telemetry_buffer_size: int = 20
    radio_parameters: RadioParameters = field(default_factory=RadioParameters)
    approved_callsigns: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if len(self.approved_callsigns) == 0:
            raise ValueError("You must provide at least one approved callsign.")
        if self.telemetry_buffer_size < 1:
            raise ValueError("Telemetry buffer size must be a positive integer.")

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new Config object from the JSON data contained in the user config file."""

        return cls(
            organization=data.get("organization", cls.organization),
            rocket_name=data.get("rocket_name", cls.rocket_name),
            telemetry_buffer_size=data.get("telemetry_buffer_size", cls.telemetry_buffer_size),
            radio_parameters=RadioParameters.from_json(data.get("radio_params", dict())),  # type:ignore
            approved_callsigns=data.get("approved_callsigns", dict()),  # type:ignore
        )


def load_config(filepath: str) -> Config:
    """Returns a Config object created from a configuration JSON file. File path must relative to project directory"""
    filepath = os.path.join(Path(__file__).parents[2], filepath)
    with open(filepath, "r") as file:
        data = json.load(file)

    return Config.from_json(data)
