# Contains the logic for unpacking user configuration file
__author__ = "Thomas Selwyn"

# Imports
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Self

# Types
JSON = dict[str, Any]




@dataclass
class FaultThresholds:
    """Contains settings for fault thresholds."""

    general: dict[str, int] = field(default_factory=dict)
    altitude: dict[str, dict[str, int]] = field(default_factory=dict)
    mpu9250_imu: dict[str, dict[str, int]] = field(default_factory=dict)
    gnss: dict[str, dict[str, int]] = field(default_factory=dict)
    gnss_meta: dict[str, dict[str, int]] = field(default_factory=dict)

    def __post_init__(self):
        if len(self.altitude) == 0:
            raise ValueError("You must provide at least one fault threshold.")

    @classmethod
    def from_json(cls, data: JSON) -> Self:
        """Creates a new FaultThresholds object from the JSON data contained in the user config file."""

        return cls(
            general=data.get("general", dict()),
            altitude=data.get("altitude", dict()),
            #altitude: AltitudeThresholds = field(default_factory=AltitudeThresholds)
            mpu9250_imu=data.get("mpu9250_imu", dict()),
            gnss=data.get("gnss", dict()),
            gnss_meta=data.get("gnss_meta", dict())
        )


def load_thresholds(filepath: str) -> FaultThresholds:
    """Returns a FaultThresholds object created from a configuration JSON file."""

    with open(filepath, "r") as file:
        data = json.load(file)

    return FaultThresholds.from_json(data)
