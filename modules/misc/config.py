# Contains the logic for unpacking user configuration file
__author__ = "Matteo Golin"

# Imports
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Self

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
    LORA = "lora"
    FSK = "fsk"


class CodingRates(StrEnum):
    FOUR_FIFTHS = "4/5"
    FOUR_SIXTHS = "4/6"
    FOUR_SEVENTHS = "4/7"
    FOUR_EIGHTS = "4/8"


@dataclass
class RadioParameters:
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
        if self.frequency not in range(*LF_RANGE) and self.frequency not in range(
            *HF_RANGE
        ):
            raise ValueError(
                f"Frequency '{self.frequency}' not in low frequency range {LF_RANGE} "
                f"or high frequency range {HF_RANGE}"
            )

        if self.power not in range(*POWER_RANGE):
            raise ValueError(
                f"Power '{self.power}' not within allowed range {POWER_RANGE}"
            )

        if self.spread_factor not in VALID_SPREADING_FACTORS:
            raise ValueError(
                f"Spread factor '{self.spread_factor}' invalid; must be one of {VALID_SPREADING_FACTORS}"
            )

        if self.preamble_len not in range(*PREAMBLE_RANGE):
            raise ValueError(
                f"Preamble length '{self.preamble_len}' not within allowed range of {PREAMBLE_RANGE}"
            )

        if int(self.sync_word, 16) not in range(*SYNC_RANGE):
            raise ValueError(
                f"Sync word '{self.sync_word}' not within allowed range of {SYNC_RANGE}"
            )

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Builds a new RadioParameters object from JSON data found in a config file."""

        # Radio parameters are either initialized with an explicitly defined value from the config file, or
        # are assigned a default value.
        return cls(
            modulation=ModulationModes[data.get("modulation", "lora")],
            frequency=data.get("frequency", 433_050_000),
            power=data.get("power", 15),
            spread_factor=data.get("spread_factor", 9),
            coding_rate=CodingRates[data.get("coding_rate", "4/7")],
            bandwidth=data.get("bandwidth", 500),
            preamble_len=data.get("preamble_len", 6),
            cyclic_redundancy=data.get("cyclic_redundancy", True),
            iqi=data.get("iqi", False),
            sync_word=data.get("sync_word", "0x43"),
        )


@dataclass
class Config:
    radio_parameters: RadioParameters
    approved_callsigns: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.approved_callsigns is None or len(self.approved_callsigns) == 0:
            raise ValueError("You must provide at least one approved callsign.")

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new Config object from the JSON data contained in the user config file."""

        return cls(
            radio_parameters=RadioParameters.from_json(
                data.get("radio_params", dict())
            ),
            approved_callsigns=data.get("approved_callsigns", dict()),
        )
