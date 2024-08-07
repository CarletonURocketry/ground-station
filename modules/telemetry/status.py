from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

# Constants
MISSIONS_DIR: str = "missions"
MISSION_EXTENSION: str = "mission"


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
            self.mission_list.append(
                MissionEntry(
                    name=mission_file.stem, length=sum(1 for _ in open(mission_file)), filepath=mission_file, version=1
                )
            )

    def __iter__(self):
        yield "state", self.state
        yield "speed", self.speed,
        yield "mission_list", [dict(e) for e in self.mission_list]


@dataclass
class TelemetryStatus:
    """The status data packet for the telemetry process."""

    mission: MissionData = field(default_factory=MissionData)
    serial: SerialData = field(default_factory=SerialData)
    rn2483_radio: RN2483RadioData = field(default_factory=RN2483RadioData)
    replay: ReplayData = field(default_factory=ReplayData)

    def __iter__(self):
        yield "mission", dict(self.mission),
        yield "serial", dict(self.serial),
        yield "rn2483_radio", dict(self.rn2483_radio),
        yield "replay", dict(self.replay),
