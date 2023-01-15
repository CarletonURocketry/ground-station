# Contains the status data object class
__author__ = "Matteo Golin"

# Imports
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Protocol, Self

import data_block as dblock

# Constants
JSON = dict[str, Any]

# Helper classes
class MissionState(IntEnum):

    """The state of the mission."""

    DNE: int = -1
    LIVE: int = 0
    RECORDED: int = 1
    TEST: int = 2


class Serializable(Protocol):

    """A class which can be converted to JSON."""

    def to_json(self) -> JSON:
        """Returns the JSON representation of the class."""
        ...


# Status packet classes
@dataclass
class SerialData:

    """The serial data packet for the telemetry process."""
    available_ports: list[str] = field(default_factory=list)

    def to_json(self) -> JSON:

        return {
            "available_ports": self.available_ports
        }


@dataclass
class RN2483RadioData:

    """The RN3483 radio data packet for the telemetry process."""

    connected: bool = False
    connected_port: str = ""
    
    def to_json(self) -> JSON:

        return {
            "connected": self.connected,
            "connected_port": self.connected_port
        }


@dataclass
class MissionData:

    """The mission data packet for the telemetry process."""

    name: str = ""
    epoch: int = -1
    state: MissionState = MissionState.DNE
    recording: bool = False

    def to_json(self) -> JSON:

        return {
            "name": self.name,
            "epoch": self.epoch,
            "state": self.state.value,
            "recording": self.recording
        }


@dataclass
class RocketData:

    """The rocket data packet for the telemetry process."""

    kx134_state: int = -1
    altimeter_state: int = -1
    imu_state: int = -1
    sd_driver_state: int = -1
    deployment_state: dblock.DeploymentState = dblock.DeploymentState.DEPLOYMENT_STATE_DNE
    blocks_recorded: int = -1
    checkouts_missed: int = -1
    mission_time: int = -1
    last_mission_time: int = -1

    @classmethod
    def from_data_block(cls, data: dblock.StatusDataBlock) -> Self:

        """Creates a rocket data packet from a StatusDataBlock class."""

        return cls(
            mission_time=data.mission_time,
            kx134_state=data.kx134_state,
            altimeter_state=data.alt_state,
            imu_state=data.imu_state,
            sd_driver_state=data.sd_state,
            deployment_state=data.deployment_state,
            blocks_recorded=data.sd_blocks_recorded,
            checkouts_missed=data.sd_checkouts_missed
        )

    def to_json(self) -> JSON:

        return {
            "kx134_state": self.kx134_state,
            "altimeter_state": self.altimeter_state,
            "imu_state": self.imu_state,
            "sd_driver_state": self.sd_driver_state,
            "deployment_state": self.deployment_state.value,
            "deployment_state_text": str(self.deployment_state),
            "blocks_recorded": self.blocks_recorded,
            "checkouts_missed": self.checkouts_missed,
            "mission_time": self.mission_time,
            "last_mission_time": self.last_mission_time,
        }


@dataclass
class StatusData:

    """The status data packet for the telemetry process."""

    mission: MissionData = field(default_factory=MissionData)
    serial: SerialData = field(default_factory=SerialData)
    rn3483_radio: RN2483RadioData = field(default_factory=RN2483RadioData)
    rocket: RocketData = field(default_factory=RocketData)

    def to_json(self) -> JSON:

        return {
            "mission": self.mission.to_json(),
            "serial": self.serial.to_json(),
            "rn3483_radio": self.rn3483_radio.to_json(),
            "rocket": self.rocket.to_json(),
        }


if __name__ == '__main__':
    rocket = RocketData()
    print(rocket.to_json())
