# Contains the status data object class
__author__ = "Matteo Golin"

# Imports
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Self

import modules.telemetry.data_block as data_block
from modules.telemetry.block import SDBlockClassType
from modules.telemetry.sd_block import SDBlockException
from modules.telemetry.replay import parse_sd_block_header
from modules.telemetry.superblock import SuperBlock

# Constants
MISSION_EXTENSION: str = "mission"
MISSIONS_DIR: str = "missions"
MISSION_ENTRY = dict["name": "", "length": 0, "blocks": 0, "timestamp": 0]


# Helper classes
class MissionState(IntEnum):
    """The state of the mission."""

    DNE = -1
    LIVE = 0
    RECORDED = 1


class ReplayState(IntEnum):
    """Represents the state of the mission being currently replayed."""

    DNE = -1
    PAUSED = 0
    PLAYING = 1
    FINISHED = 2


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
    snr: int = 0  # TODO SET SNR

    def __iter__(self):
        yield "connected", self.connected,
        yield "connected_port", self.connected_port
        yield "snr", self.snr


@dataclass
class MissionData:
    """The mission data packet for the telemetry process."""

    name: str = ""
    epoch: int = -1
    state: MissionState = MissionState.DNE
    recording: bool = False
    last_mission_time: int = -1

    def __iter__(self):
        yield "name", self.name,
        yield "epoch", self.epoch,
        yield "state", self.state.value,
        yield "recording", self.recording
        yield "last_mission_time", self.last_mission_time


@dataclass
class RocketData:
    """The rocket data packet for the telemetry process."""

    mission_time: int = -1
    kx134_state: int = -1
    altimeter_state: int = -1
    imu_state: int = -1
    sd_driver_state: int = -1
    deployment_state: data_block.DeploymentState = data_block.DeploymentState.DEPLOYMENT_STATE_DNE
    blocks_recorded: int = -1
    checkouts_missed: int = -1

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
        yield "mission_time", self.mission_time,
        yield "kx134_state", self.kx134_state,
        yield "altimeter_state", self.altimeter_state,
        yield "imu_state", self.imu_state,
        yield "sd_driver_state", self.sd_driver_state,
        yield "deployment_state", self.deployment_state.value,
        yield "blocks_recorded", self.blocks_recorded,
        yield "checkouts_missed", self.checkouts_missed,


# Replay packet class
@dataclass
class ReplayData:
    """The replay data packet for the telemetry process."""

    state: ReplayState = ReplayState.DNE
    speed: float = 1.0
    last_played_speed = 1.0
    mission_files_list = [""]
    mission_list: list[MISSION_ENTRY] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Update the mission list on creation
        self.update_mission_list()

    def update_mission_list(self, missions_dir: Path = Path.cwd().joinpath(MISSIONS_DIR)) -> None:
        """Gets the available mission recordings from the mission folder."""

        # TODO change this so that mission_extension and directory are not defined in multiple files
        self.mission_files_list = [name for name in missions_dir.glob(f"*.{MISSION_EXTENSION}") if name.is_file()]

        # Check each file to output its misc details
        self.mission_list = []
        for filename in self.mission_files_list:
            with open(f"{missions_dir.joinpath(filename)}", "rb") as file:
                # Reads superblock for flight details
                superblock_bytes = file.read(512)
                if len(superblock_bytes) != 512:
                    print(f"Superblock for {filename.name} contains {len(superblock_bytes)} byte(s)")
                    continue

                mission_sb = SuperBlock.from_bytes(superblock_bytes)

                if len(mission_sb.flights) == 0:
                    print(f"Flight list for {filename.name} is empty")
                    continue

                mission_time = 0
                # Reads last telemetry block of each flight to get final mission time
                for flight in mission_sb.flights:
                    file.seek(flight.first_block * 512)
                    mission_time += get_last_mission_time(file, flight.num_blocks)

                # Output mission to mission list
                mission_entry = {"name": filename.stem, "length": mission_time,
                                 "epoch": mission_sb.flights[0].timestamp}
                self.mission_list.append(mission_entry)

    def __iter__(self):
        yield "state", self.state
        yield "speed", self.speed,
        yield "mission_list", self.mission_list


@dataclass
class StatusData:
    """The status data packet for the telemetry process."""

    mission: MissionData = field(default_factory=MissionData)
    serial: SerialData = field(default_factory=SerialData)
    rn2483_radio: RN2483RadioData = field(default_factory=RN2483RadioData)
    rocket: RocketData = field(default_factory=RocketData)
    replay: ReplayData = field(default_factory=ReplayData)

    def __iter__(self):
        yield "mission", dict(self.mission),
        yield "serial", dict(self.serial),
        yield "rn2483_radio", dict(self.rn2483_radio),
        yield "rocket", dict(self.rocket),
        yield "replay", dict(self.replay),


class ParsingException(Exception):
    pass


def get_last_mission_time(file, num_blocks) -> int:
    """ Obtains last recorded telemetry mission time from a flight"""

    # If flight is empty, return
    if num_blocks == 0:
        return 0

    count = 0
    last_mission_time = 0

    while count <= ((num_blocks * 512) - 4):

        try:
            block_header = file.read(4)
            block_class, block_subtype, block_length = parse_sd_block_header(block_header)
            block_data = file.read(block_length - 4)
        except SDBlockException:
            return 0

        count = count + block_length
        if count > (num_blocks * 512):
            raise ParsingException(f"Read block of length {block_length} would read {count} bytes "
                                   f"from {num_blocks * 512} byte flight")

        # Do not unnecessarily parse blocks unless close to end of flight
        if count > ((num_blocks - 1) * 512) and block_class == SDBlockClassType.TELEMETRY_DATA:
            # First four bytes in block data is always mission time.
            block_time = struct.unpack("<I", block_data[:4])[0]
            last_mission_time = block_time

    return last_mission_time
