# Contains the status data object class
__author__ = "Matteo Golin"

# Imports
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Self
from pathlib import Path

import modules.telemetry.data_block as data_block
from modules.telemetry.block import DataBlockSubtype
from modules.telemetry.sd_block import SDBlockException, SDBlock, TelemetryDataBlock
from modules.telemetry.superblock import SuperBlock, Flight

# Constants
MISSION_EXTENSION: str = "cuinspace"
MISSIONS_DIR: str = "missions"
MISSION_ENTRY = dict["name": "", "length": 0, "blocks": 0, "timestamp": 0]


# Helper classes
class MissionState(IntEnum):
    """The state of the mission."""

    DNE = -1
    LIVE = 0
    RECORDED = 1
    TEST = 2


class ReplayState(StrEnum):
    """Represents the state of the mission being currently replayed."""

    DNE = ""
    PAUSED = "paused"
    PLAYING = "playing"


# Status packet classes
@dataclass
class SerialData:
    """The serial data packet for the telemetry process."""
    available_ports: list[str] = field(default_factory=list)

    def __iter__(self):
        yield "available_ports", self.available_ports


@dataclass
class RN2483RadioData:
    """The RN2483 radio data packet for the telemetry process."""

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
    deployment_state: data_block.DeploymentState = data_block.DeploymentState.DEPLOYMENT_STATE_DNE
    blocks_recorded: int = -1
    checkouts_missed: int = -1
    mission_time: int = -1
    last_mission_time: int = -1

    @classmethod
    def from_data_block(cls, data: data_block.StatusDataBlock) -> Self:
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
        yield "blocks_recorded", self.blocks_recorded,
        yield "checkouts_missed", self.checkouts_missed,
        yield "mission_time", self.mission_time,
        yield "last_mission_time", self.last_mission_time,


@dataclass
class StatusData:
    """The status data packet for the telemetry process."""

    mission: MissionData = field(default_factory=MissionData)
    serial: SerialData = field(default_factory=SerialData)
    rn2483_radio: RN2483RadioData = field(default_factory=RN2483RadioData)
    rocket: RocketData = field(default_factory=RocketData)

    def __iter__(self):
        yield "mission", dict(self.mission),
        yield "serial", dict(self.serial),
        yield "rn2483_radio", dict(self.rn2483_radio),
        yield "rocket", dict(self.rocket),


class ParsingException(Exception):
    pass


def get_last_mission_time(file, num_blocks):
    """ Obtains last recorded telemetry mission time from a flight"""

    # Seek to start of flight
    count = 0
    last_mission_time = None

    while count <= ((num_blocks * 512) - 4):
        header = file.read(4)

        try:
            block_length = SDBlock.parse_length(header)
        except SDBlockException:
            return

        count = count + block_length
        if count > (num_blocks * 512):
            raise ParsingException(f"Read block of length {block_length} would read {count} bytes "
                                   f"from {num_blocks * 512} byte flight")

        block = header + file.read(block_length - 4)

        # Do not unnecessarily parse blocks unless close to end of flight
        if count > ((num_blocks - 1) * 512):
            SDBlockObj = SDBlock.from_bytes(block)
            if type(SDBlockObj) == TelemetryDataBlock:
                last_mission_time = SDBlockObj.data.mission_time
    return last_mission_time


# Replay packet class
@dataclass
class ReplayData:
    """The replay data packet for the telemetry process."""

    status: ReplayState = ReplayState.DNE
    speed: float = 1.0
    mission_files_list = [""]
    mission_list: list[MISSION_ENTRY] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.update_mission_list()  # Update the mission list on creation

    def update_mission_list(self, missions_dir: Path = Path.cwd().joinpath(MISSIONS_DIR)) -> None:
        """Gets the available mission recordings from the mission folder."""

        # TODO change this so that mission_extension and directory are not defined in multiple files
        self.mission_files_list = [name for name in missions_dir.glob(f"*.{MISSION_EXTENSION}") if name.is_file()]

        # Check each file to output its misc details
        for filename in self.mission_files_list:
            with open(f"{missions_dir.joinpath(filename)}", "rb") as file:
                # Reads superblock for flight details
                mission_sb = SuperBlock(file.read(512))
                first_flight = mission_sb.flights[0]

                # Reads last telemetry block of flight to get final mission time
                file.seek(first_flight.first_block * 512)
                mission_time = get_last_mission_time(file, first_flight.num_blocks)

                # Output mission to mission list
                mission_entry = {"name": filename.stem, "length": mission_time,
                                 "timestamp": first_flight.timestamp}
                self.mission_list.append(mission_entry)

    def __iter__(self):
        yield "status", self.status.value
        yield "speed", self.speed,
        yield "mission_list", self.mission_list
