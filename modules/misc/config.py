# Contains the logic for unpacking user configuration file
__author__ = "Matteo Golin"

# Imports
import json
from dataclasses import dataclass, field
from enum import StrEnum
from json import JSONDecodeError
from typing import Any, Self
import logging

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

# Set up logging
logger = logging.getLogger(__name__)


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
    cyclic_redundancy: Enable or disable cyclic redundancy check used to detect errors in the received signal.
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
class FaultsThresholds:
    """Contains settings for fault thresholds."""

    general: dict[str, int] = field(default_factory=dict)
    rocket: dict[str, dict[int]] = field(default_factory=dict)
    altitude: dict[str, int] = field(default_factory=dict)
    mpu9250_imu: dict[str, int] = field(default_factory=dict)
    gnss: dict[str, int] = field(default_factory=dict)
    gnss_meta: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new FaultThresholds object from the JSON data contained in the fault thresholds file."""

        return cls(
            general=data.get("general", dict()),  # type:ignore
            rocket=data.get("rocket", dict()),  # type:ignore
            altitude=data.get("altitude", dict()),  # type:ignore
            mpu9250_imu=data.get("mpu9250_imu", dict()),  # type:ignore
            gnss=data.get("gnss", dict()),  # type:ignore
            gnss_meta=data.get("gnss_meta", dict()),  # type:ignore
        )


@dataclass
class Faults:
    """
    Represents a collection of parameters for fault thresholds.
    """

    enabled: bool = True
    filename: str = "launch_canada.json"
    thresholds: FaultsThresholds = field(default_factory=FaultsThresholds)

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Builds a new Faults object from JSON data found in a config file."""
        cls.enabled = data.get("enabled", True)
        cls.filename = data.get("filename", "launch_canada.json")

        try:
            with open(cls.filename, "r") as file:
                data = json.load(file)
                cls.thresholds = FaultsThresholds.from_json(data)
        except JSONDecodeError:
            logger.error("Unable to load fault thresholds due to corrupted config. Fault monitoring disabled.")
            cls.enabled = False
        except FileNotFoundError:
            logger.error("Fault thresholds file not found. Fault monitoring disabled.")
            cls.enabled = False
        return cls

    def __iter__(self):
        yield "enabled", self.enabled
        yield "filename", self.filename
        yield "thresholds", self.thresholds


@dataclass
class Config:
    """Contains settings for the ground station process."""

    telemetry_buffer_size: int = 20
    faults: Faults = field(default_factory=Faults)
    radio_parameters: RadioParameters = field(default_factory=RadioParameters)
    approved_callsigns: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if len(self.approved_callsigns) == 0:
            raise ValueError("You must provide at least one approved callsign.")

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new Config object from the JSON data contained in the user config file."""

        return cls(
            telemetry_buffer_size=data.get("telemetry_buffer_size", int(20)),
            faults=Faults.from_json(data.get("faults", dict())),  # type:ignore
            radio_parameters=RadioParameters.from_json(data.get("radio_params", dict())),  # type:ignore
            approved_callsigns=data.get("approved_callsigns", dict()),  # type:ignore
        )


def load_config(filepath: str) -> Config:
    """Returns a Config object created from a configuration JSON file."""

    with open(filepath, "r") as file:
        data = json.load(file)

    return Config.from_json(data)
