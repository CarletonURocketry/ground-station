# Contains the status data object class
__author__ = "Matteo Golin"

# Imports
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Self
from pathlib import Path

import modules.telemetry.data_block as dblock

# Constants
MISSION_EXTENSION: str = ".mission"
MISSIONS_DIR: str = "missions"


# Helper classes
class MissionState(IntEnum):

    """The state of the mission."""

    DNE: int = -1
    LIVE: int = 0
    RECORDED: int = 1
    TEST: int = 2


class ReplayState(StrEnum):

    """Represents the state of the mission being currently replayed."""

    DNE: str = ""
    PAUSED: str = "paused"
    PLAYING: str = "playing"


# Status packet classes
@dataclass
class SerialData:

    """The serial data packet for the telemetry process."""
    available_ports: list[str] = field(default_factory=list)

    def __iter__(self):
        yield "available_ports", self.available_ports


@dataclass
class RN2483RadioData:

    """The RN3483 radio data packet for the telemetry process."""

    connected: bool = False
    connected_port: str = ""
    
    def __iter__(self):
        yield "connected", self.connected,
        yield "connected_port", self.connected_port


@dataclass
class MissionData:

    """The mission data packet for the telemetry process."""

    name: str = ""
    epoch: int = -1
    state: MissionState = MissionState.DNE
    recording: bool = False

    def __iter__(self):
        yield "name", self.name,
        yield "epoch", self.epoch,
        yield "state", self.state.value,
        yield "recording", self.recording


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

    def __iter__(self):

        yield "kx134_state", self.kx134_state,
        yield "altimeter_state", self.altimeter_state,
        yield "imu_state", self.imu_state,
        yield "sd_driver_state", self.sd_driver_state,
        yield "deployment_state", self.deployment_state.value,
        yield "deployment_state_text", str(self.deployment_state),
        yield "blocks_recorded", self.blocks_recorded,
        yield "checkouts_missed", self.checkouts_missed,
        yield "mission_time", self.mission_time,
        yield "last_mission_time", self.last_mission_time,


@dataclass
class StatusData:

    """The status data packet for the telemetry process."""

    mission: MissionData = field(default_factory=MissionData)
    serial: SerialData = field(default_factory=SerialData)
    rn3483_radio: RN2483RadioData = field(default_factory=RN2483RadioData)
    rocket: RocketData = field(default_factory=RocketData)

    def __iter__(self):

        yield "mission", dict(self.mission),
        yield "serial", dict(self.serial),
        yield "rn3483_radio", dict(self.rn3483_radio),
        yield "rocket", dict(self.rocket),


# Replay packet class
@dataclass
class ReplayData:
    """The replay data packet for the telemetry process."""

    status: ReplayState = ReplayState.DNE
    speed: float = 1.0
    mission_list: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.update_mission_list()  # Update the mission list on creation

    def update_mission_list(self):
        """Gets the available mission recordings from the mission folder."""

        # TODO change this so that mission_extension and directory are not defined in multiple files
        missions_dir = Path.cwd().joinpath(MISSIONS_DIR)
        self.mission_list = [name.stem for name in missions_dir.glob(f"*{MISSION_EXTENSION}") if name.is_file()]

    def __iter__(self):

        yield "status", self.status.value
        yield "speed", self.speed,
        yield "mission_list", self.mission_list


if __name__ == '__main__':
    rocket = RocketData()
    print(dict(rocket))
