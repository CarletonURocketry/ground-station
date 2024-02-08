# Contains the logic for unpacking fault thresholds
__author__ = "Thomas Selwyn"

import json
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Any, Self, NamedTuple
from modules.misc.config import ConfigError
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Types
JSON = dict[str, Any]


class ThresholdValues(NamedTuple):
    LOW: int
    HYSTERESIS: int
    HIGH: int

    @classmethod
    def from_json(cls, data: list[int]) -> Self:
        return cls(
            LOW=int(data[0]),
            HYSTERESIS=int(data[1]),
            HIGH=int(data[2]),
        )


@dataclass
class RocketThresholds:
    altitude = ThresholdValues(LOW=-100, HYSTERESIS=9000, HIGH=12000)
    pressure = ThresholdValues(LOW=9000, HYSTERESIS=13000, HIGH=15000)
    speed = ThresholdValues(LOW=-5, HYSTERESIS=50, HIGH=200)
    temperature = ThresholdValues(LOW=0, HYSTERESIS=65, HIGH=75)

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        return cls(
            altitude=ThresholdValues.from_json(data.get("altitude", list[-100, 9000, 12000])),  # type:ignore
            pressure=ThresholdValues.from_json(data.get("pressure", list[9000, 13000, 15000])),  # type:ignore
            speed=ThresholdValues.from_json(data.get("speed", list[-5, 50, 200])),  # type:ignore
            temperature=ThresholdValues.from_json(data.get("temperature", list[0, 65, 75])),  # type:ignore
        )


@dataclass
class Thresholds:
    """Contains settings for fault thresholds."""

    general: dict[str, int] = field(default_factory=dict)
    rocket: RocketThresholds = field(default_factory=RocketThresholds)
    altitude: dict[str, int] = field(default_factory=dict)
    mpu9250_imu: dict[str, int] = field(default_factory=dict)
    gnss: dict[str, int] = field(default_factory=dict)
    gnss_meta: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new FaultThresholds object from the JSON data contained in the fault thresholds file."""

        return cls(
            general=data.get("general", dict()),  # type:ignore
            rocket=RocketThresholds.from_json(data.get("rocket", dict())),  # type:ignore
            altitude=data.get("altitude", dict()),  # type:ignore
            mpu9250_imu=data.get("mpu9250_imu", dict()),  # type:ignore
            gnss=data.get("gnss", dict()),  # type:ignore
            gnss_meta=data.get("gnss_meta", dict()),  # type:ignore
        )


def load_thresholds(filepath: str) -> Thresholds:
    """Returns a Thresholds object created from a configuration JSON file."""

    try:
        with open(filepath, "r") as file:
            data = json.load(file)
            return Thresholds.from_json(data)
    except JSONDecodeError:
        raise ConfigError("Unable to load fault thresholds due to corrupted config. Fault monitoring disabled.")
    except FileNotFoundError:
        raise ConfigError("Fault thresholds file not found. Fault monitoring disabled.")
