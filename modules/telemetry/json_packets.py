# Contains the status data object class
__author__ = "Matteo Golin"

import json

# Imports
import logging
import os
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Self, TypeAlias
import modules.telemetry.data_block as db
from modules.telemetry.telemetry_utils import ParsedBlock

# Constants
MISSION_EXTENSION: str = "mission"
MISSIONS_DIR: str = "missions"

# Aliases
OutputFormat: TypeAlias = dict[str, dict[str, dict[str, dict[str, str]]]]

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
    filepath: Path = Path.cwd() / MISSIONS_DIR
    version: int = 1
    valid: bool = False

    def __iter__(self):
        yield "name", self.name
        yield "length", self.length
        yield "version", self.version

    def __len__(self) -> int:
        return self.length

    def __bool__(self):
        return self.valid


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


@dataclass
class RocketData:
    """The rocket data packet for the telemetry process."""

    mission_time: int = -1
    deployment_state: db.DeploymentState = db.DeploymentState.DEPLOYMENT_STATE_DNE
    blocks_recorded: int = -1
    checkouts_missed: int = -1

    @classmethod
    def from_data_block(cls, data: db.StatusDataBlock) -> Self:
        """Creates a rocket data packet from a StatusDataBlock class."""

        return cls(
            mission_time=data.mission_time,
            deployment_state=data.deployment_state,
            blocks_recorded=data.sd_blocks_recorded,
            checkouts_missed=data.sd_checkouts_missed,
        )

    def __iter__(self):
        yield "mission_time", self.mission_time,
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
        for mission_file in self.mission_files_list:
            self.mission_list.append(parse_mission_file(mission_file))

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


def parse_mission_file(mission_file: Path) -> MissionEntry:
    """Obtains mission metadata from file"""

    length = 0
    with open(mission_file, "r") as file:
        for _ in file:
            length += 1

    return MissionEntry(name=mission_file.stem, length=length, filepath=mission_file, version=1)


@dataclass
class TelemetryDataPacketBlock:
    """A generic block object to store information for telemetry data
    All stored values must be updated at once!"""

    mission_time: list[int] = field(default_factory=list[int])
    stored_values: dict[str, list[int]] = field(default_factory=dict)

    def update(self, data: dict[str, int], buffer_size: int) -> None:
        """Updates the stored values with the given data
        Args:
            data (dict[str, int]) : Dictionary of data to update containing mission_time and stored_values squashed
            buffer_size (int) : Size of the telemetry buffer"""

        # Ensure you are not half updating the packet
        # As this can cause the arrays to become out of sync and meaningless.
        if dict(self).keys() != data.keys():
            logger.error("Block must be updated using a full set of values at the same time!")
            logger.debug(f"Tried updating {dict(self).keys()} using {data.keys()}!")
            return

        # Updates stored values with new values
        for key in data.keys():
            if key == "mission_time":
                self.mission_time.append(data["mission_time"])
            else:
                self.stored_values[key].append(data[key])

        # Ensure buffer sizes are kept
        # Note: This uses a while loop incase buffer size shrinks drastically
        while len(self.mission_time) > buffer_size:
            self.mission_time.pop(0)
            for key in self.stored_values.keys():
                self.stored_values[key].pop(0)

    def clear(self) -> None:
        """Clears all stored values"""
        self.mission_time = []
        self.stored_values = {key: [] for key in self.stored_values.keys()}

    def __str__(self):
        """Returns a string representation of the TelemetryDataPacketBlock"""
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, {self.stored_values}"

    def __iter__(self):
        """Returns an interator containing all the stored values"""
        yield "mission_time", self.mission_time
        for key in self.stored_values.keys():
            yield key, self.stored_values[key]


class TelemetryData:
    """Contains the output specification for the telemetry data block"""

    # Configuration
    buffer_size: int = 20
    decoder: list[dict[int, dict[str, str]]] = field(default_factory=list)

    # Current data storage
    last_mission_time: int = -1
    output_blocks: dict[str, TelemetryDataPacketBlock] = field(default_factory=dict)
    update_buffer: dict[str, dict[str, int | None]] = field(default_factory=dict)

    def __init__(self, telemetry_buffer_size: int = 20):
        """Initializes the telemetry data object
        Args:
             telemetry_buffer_size (int): The size of the data buffer"""
        logger.debug(f"Initializing TelemetryData[{telemetry_buffer_size}]")
        self.buffer_size = telemetry_buffer_size
        self.output_blocks = {}
        self.update_buffer = {}

        # Read packet definition file
        filepath = os.path.join(Path(__file__).parents[0], "telemetry_packet.json")
        with open(filepath, "r") as file:
            output_format: OutputFormat = dict(json.load(file))

        # Generate telemetry data packet from output specification
        for key in output_format.keys():
            telemetry_keys: list[str] = list(output_format[key].keys())
            self.output_blocks[key] = TelemetryDataPacketBlock(stored_values={key: [] for key in telemetry_keys})
            self.update_buffer[key] = {key: None for key in telemetry_keys}

        # Generate extremely efficient access decoder matrix
        #                                        = {INPUT: OUTPUT}     "dataPacketBlockName.storedValueVariable"
        # decoder[packet_version][block_subtype] = {"gps_sats_in_use": "sats_in_use.gps_sats_in_use"}
        self.decoder = [{}, {}, {}, {}, {}]
        for data_packet in output_format.keys():
            for stored_value in output_format[data_packet].keys():
                for version in output_format[data_packet][stored_value].keys():
                    for block in output_format[data_packet][stored_value][version].keys():
                        input_key: str = output_format[data_packet][stored_value][version][block]
                        output_key: str = f"{data_packet}.{stored_value}"

                        existing: dict[str, str] = self.decoder[int(version)].get(int(block), {})
                        existing[input_key] = output_key
                        self.decoder[int(version)][int(block)] = existing

    def update_telemetry(self, packet_version: int, blocks: list[ParsedBlock]) -> None:
        """Updates telemetry object from given parsed blocks
        Args:
            packet_version (int): The packet encoding version
            blocks (list[ParsedBlock]): A list of parsed block objects"""

        # Extract block data
        for block in blocks:
            block_num: int = block.block_header.message_subtype
            block_decode: dict[str, str] = self.decoder[packet_version][block_num]
            data: dict[str, int | dict[str, int]] = block.block_contents

            logger.debug(f"{block}")

            try:
                # Update last mission time
                if data["mission_time"] > self.last_mission_time:  # type: ignore
                    self.last_mission_time = data["mission_time"]  # type: ignore

                # Grab input values and put them in update buffer (to fill output packets)
                for key in block_decode.keys():
                    destinationBlock: str = block_decode[key].split(".")[0]
                    destinationValue: str = block_decode[key].split(".")[1]
                    # Extract data and associated mission time to buffer
                    self.update_buffer[destinationBlock]["mission_time"] = data["mission_time"]  # type: ignore
                    if "." in key:
                        datakey: str = key.split(".")[0]
                        datasubkey: str = key.split(".")[1]
                        self.update_buffer[destinationBlock][destinationValue] = data[datakey][  # type: ignore
                            datasubkey
                        ]
                    else:
                        self.update_buffer[destinationBlock][destinationValue] = data[key]  # type: ignore

                # Check if we filled any packet during this block extraction
                for key in self.update_buffer.keys():
                    if None not in self.update_buffer[key].values():
                        # Let's update packet
                        self.output_blocks[key].update(self.update_buffer[key], self.buffer_size)  # type: ignore
                        # Clear packets buffer
                        for subkey in self.update_buffer[key].keys():
                            self.update_buffer[key][subkey] = None
            except KeyError as e:
                logger.error(f"Telemetry parsed block data issue. Missing key {e}")

    def update_buffer_size(self, new_buffer_size: int = 20) -> None:
        """Allows updating the telemetry buffer size without recreating object"""
        self.buffer_size = new_buffer_size

    def clear(self) -> None:
        """Clears the telemetry output data packet entirely"""
        self.last_mission_time = -1
        # Clear buffer
        for dest_block in self.update_buffer.keys():
            for dest_value in self.update_buffer[dest_block].keys():
                self.update_buffer[dest_block][dest_value] = None
        # Clear packet blocks
        for block in self.output_blocks.values():
            block.clear()

    def __iter__(self):
        """Returns an interator containing all the packets"""
        yield "last_mission_time", self.last_mission_time
        for key in self.output_blocks.keys():
            yield key, dict(self.output_blocks[key])
