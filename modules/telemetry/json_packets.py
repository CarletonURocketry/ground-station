# Contains the status data object class
__author__ = "Matteo Golin"

# Imports
from io import BufferedReader
import logging
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Self

import modules.telemetry.data_block as db
from modules.telemetry.block import SDBlockSubtype
from modules.telemetry.sd_block import SDBlockException
from modules.telemetry.replay import parse_sd_block_header
from modules.telemetry.superblock import find_superblock

# Constants
MISSION_EXTENSION: str = "mission"
MISSIONS_DIR: str = "missions"

logger = logging.getLogger(__name__)


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


@dataclass
class MissionEntry:
    """Represents an available mission for replay."""

    name: str
    length: int = 0
    epoch: int = 0
    valid: bool = True

    def __iter__(self):
        yield "name", self.name
        yield "length", self.length
        yield "epoch", self.epoch
        yield "valid", self.valid

    def __len__(self) -> int:
        return self.length

    def __bool__(self):
        return bool(self.valid)


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
    deployment_state: db.DeploymentState = db.DeploymentState.DEPLOYMENT_STATE_DNE
    blocks_recorded: int = -1
    checkouts_missed: int = -1

    @classmethod
    def from_data_block(cls, data: db.StatusDataBlock) -> Self:
        """Creates a rocket data packet from a StatusDataBlock class."""

        return cls(
            mission_time=data.mission_time,
            kx134_state=data.kx134_state,
            altimeter_state=data.alt_state,
            imu_state=data.imu_state,
            sd_driver_state=data.sd_state,
            deployment_state=data.deployment_state,
            blocks_recorded=data.sd_blocks_recorded,
            checkouts_missed=data.sd_checkouts_missed,
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
    last_played_speed: float = 1.0
    mission_files_list: list[Path] = field(default_factory=list)
    mission_list: list[MissionEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Update the mission list on creation
        self.update_mission_list()

    def update_mission_list(self, missions_dir: Path = Path.cwd().joinpath(MISSIONS_DIR)) -> None:
        """Gets the available mission recordings from the mission folder."""

        # TODO change this so that mission_extension and directory are not defined in multiple files
        self.mission_files_list = [file for file in missions_dir.glob(f"*.{MISSION_EXTENSION}") if file.is_file()]

        # Check each file to output its misc details
        self.mission_list = []
        for filename in self.mission_files_list:
            mission_path: Path = missions_dir.joinpath(filename.name)
            self.mission_list.append(parse_mission_file(mission_path))

    def __iter__(self):
        yield "state", self.state
        yield "speed", self.speed,
        yield "mission_list", [dict(e) for e in self.mission_list]


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


def get_last_mission_time(file: BufferedReader, num_blocks: int) -> int:
    """Obtains last recorded telemetry mission time from a flight"""

    # If flight is empty, return no time found
    if num_blocks <= 0:
        return -1

    count = 0
    last_mission_time = 0

    while count <= ((num_blocks * 512) - 4):
        try:
            block_header: bytes = file.read(4)
            block_class, _, block_length = parse_sd_block_header(block_header)
            block_data = file.read(block_length - 4)
        except SDBlockException:
            return last_mission_time
        except ValueError:
            return last_mission_time

        count += block_length
        if count > (num_blocks * 512):
            raise ParsingException(
                f"Read block of length {block_length} would read {count} bytes from {num_blocks * 512} byte flight"
            )

        # Do not unnecessarily parse blocks unless close to end of flight
        is_telem = block_class == SDBlockSubtype.TELEMETRY_DATA
        if count > ((num_blocks - 1) * 512) and is_telem:
            # First four bytes in block data is always mission time.
            block_time = struct.unpack("<I", block_data[:4])[0]
            last_mission_time = block_time if block_time > last_mission_time else last_mission_time

    return last_mission_time


def parse_mission_file(mission_file: Path) -> MissionEntry:
    """Obtains mission metadata from file"""

    # Find superblock from file and return it
    superblock_result = find_superblock(mission_file)

    # Parameters
    mission_length = 0
    mission_epoch = -1

    if superblock_result is None:
        return MissionEntry(mission_file.stem, mission_length, mission_epoch, False)

    sb_addr, mission_sb = superblock_result

    # Check if flight list is empty
    if mission_sb.flights:
        mission_epoch = mission_sb.flights[0].timestamp
    else:
        logger.warning(f"Flight list for {mission_file.stem} is empty")
        return MissionEntry(mission_file.stem, mission_length, mission_epoch, False)

    # Read mission length
    try:
        with open(f"{mission_file}", "rb") as file:
            # Reads last telemetry block of each flight to get final mission time
            for flight in mission_sb.flights:
                _ = file.seek((sb_addr + flight.first_block) * 512)
                mission_length += get_last_mission_time(file, flight.num_blocks)
    except ParsingException:
        logger.info(f"Unable to parse mission length from {mission_file.stem}, defaulting to -1")

    # Return mission entry
    return MissionEntry(name=mission_file.stem, length=mission_length, epoch=mission_epoch, valid=True)
