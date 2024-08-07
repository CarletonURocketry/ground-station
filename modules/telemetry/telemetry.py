"""
Telemetry to parse radio packets, keep history and to log everything.
Incoming information comes from rn2483_radio_payloads in payload format.
Outputs information to telemetry_json_output in friendly JSON for UI.
"""

from io import BufferedWriter
import logging
from ast import literal_eval
from queue import Queue
import multiprocessing as mp
from multiprocessing import Process, active_children
from pathlib import Path
from signal import signal, SIGTERM
from time import sleep
from typing import Any, TypeAlias
from types import FrameType

from modules.telemetry.data import TelemetryData
from modules.telemetry.status import TelemetryStatus, MissionState, ReplayState
import modules.telemetry.websocket_commands as wsc
from modules.misc.config import Config
from modules.telemetry.replay import TelemetryReplay
from modules.telemetry.parsing_utils import parse_rn2483_transmission, ParsedTransmission
from modules.telemetry.errors import MissionNotFoundError, AlreadyRecordingError, ReplayPlaybackError

# Constants
MISSION_EXTENSION: str = "mission"

# Types
JSON: TypeAlias = dict[str, Any]

# Set up logging
logger = logging.getLogger(__name__)


def shutdown_sequence(signum: int, stack_frame: FrameType) -> None:
    """Kills all children before terminating. Acts as a signal handler for Telemetry class when receiving SIGTERM."""
    for child in active_children():
        child.terminate()
    exit(0)


class Telemetry:
    def __init__(
        self,
        serial_status: Queue[str],
        rn2483_radio_payloads: Queue[Any],
        rn2483_radio_input: Queue[str],
        radio_signal_report: Queue[str],
        telemetry_json_output: Queue[JSON],
        telemetry_ws_commands: Queue[list[str]],
        config: Config,
        version: str,
    ):
        super().__init__()
        # Multiprocessing Queues to communicate with SerialManager and WebSocketHandler processes
        self.serial_status: Queue[str] = serial_status
        self.rn2483_radio_payloads: Queue[str] = rn2483_radio_payloads
        self.rn2483_radio_input: Queue[str] = rn2483_radio_input
        self.radio_signal_report: Queue[str] = radio_signal_report
        self.telemetry_json_output: Queue[JSON] = telemetry_json_output
        self.telemetry_ws_commands: Queue[list[str]] = telemetry_ws_commands

        self.config = config
        self.version = version

        # Telemetry Status holds the current status of the telemetry backend
        # Telemetry Data holds the last few copies of received data blocks stored under the subtype name as a key.
        self.status: TelemetryStatus = TelemetryStatus()
        self.telemetry_data: TelemetryData = TelemetryData(self.config.telemetry_buffer_size)

        # Mission File System
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path: Path | None = None

        # Mission Recording (not in use)
        self.mission_recording_file: BufferedWriter | None = None
        self.mission_recording_buffer: bytearray = bytearray(b"")

        # Replay System
        self.replay = None
        self.replay_input: Queue[str] = mp.Queue()  # type:ignore
        self.replay_output: Queue[str] = mp.Queue()  # type:ignore

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)  # type:ignore

        # Start Telemetry
        self.update_websocket()
        self.run()

    def run(self):
        while True:
            # Sleep for 1 ms
            sleep(0.001)

            while not self.telemetry_ws_commands.empty():
                try:
                    # Parse websocket command into an enum
                    commands: list[str] = self.telemetry_ws_commands.get()
                    command = wsc.parse(commands, wsc.WebsocketCommand)
                    parameters = commands  # Remaining items in the commands list are parameters
                    self.execute_command(command, parameters)
                except AttributeError as e:
                    logger.error(e)
                except wsc.WebsocketCommandNotFound as e:
                    logger.error(e)

            while not self.radio_signal_report.empty():
                # TODO set radio SNR
                logger.info(f"SIGNAL DATA {self.radio_signal_report.get()}")

            while not self.serial_status.empty():
                x = self.serial_status.get().split(" ", maxsplit=1)
                logger.debug(f"serial_status: {x}")
                self.parse_serial_status(command=x[0], data=x[1])
                self.update_websocket()

            # Switch data queues between replay and radio depending on mission state
            match self.status.mission.state:
                case MissionState.RECORDED:
                    while not self.replay_output.empty():
                        self.process_transmission(self.replay_output.get())
                        self.update_websocket()
                case _:
                    while not self.rn2483_radio_payloads.empty():
                        self.process_transmission(self.rn2483_radio_payloads.get())
                        self.update_websocket()

    def update_websocket(self) -> None:
        """Updates the websocket with the latest packet using the JSON output process."""
        websocket_response = {
            "org": self.config.organization,
            "rocket": self.config.rocket_name,
            "version": self.version,
            "status": dict(self.status),
            "telemetry": dict(self.telemetry_data),
        }
        self.telemetry_json_output.put(websocket_response)

    def reset_data(self) -> None:
        """Resets all live data on the telemetry backend to a default state."""
        self.status = TelemetryStatus()
        self.telemetry_data.clear()

    def parse_serial_status(self, command: str, data: str) -> None:
        """Parses the serial managers status output"""
        match command:
            case "serial_ports":
                self.status.serial.available_ports = literal_eval(data)
            case "rn2483_connected":
                self.status.rn2483_radio.connected = bool(data)
            case "rn2483_port":
                if self.status.mission.state != MissionState.DNE:
                    self.reset_data()
                self.status.rn2483_radio.connected_port = data

                match self.status.rn2483_radio.connected_port:
                    case "":
                        self.status.mission.state = MissionState.DNE
                    case _:
                        self.status.mission.state = MissionState.LIVE
            case _:
                return None

    def execute_command(self, command: wsc.Enum, parameters: list[str]) -> None:
        """Executes the passed websocket command."""

        WSCommand = wsc.WebsocketCommand
        match command:
            case WSCommand.UPDATE:
                self.status.replay.update_mission_list()

            # Replay commands
            case WSCommand.REPLAY.value.PLAY:
                if not parameters:
                    raise ReplayPlaybackError
                mission_name = " ".join(parameters)
                try:
                    self.play_mission(mission_name)
                except MissionNotFoundError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)
            case WSCommand.REPLAY.value.PAUSE:
                self.set_replay_speed(0.0)
            case WSCommand.REPLAY.value.RESUME:
                self.set_replay_speed(self.status.replay.last_played_speed)
            case WSCommand.REPLAY.value.SPEED:
                self.set_replay_speed(float(parameters[0]))
            case WSCommand.REPLAY.value.STOP:
                self.stop_replay()

            # Record commands
            case WSCommand.RECORD.value.STOP:
                self.stop_recording()
            case WSCommand.RECORD.value.START:
                # If there is no mission name, use the default
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.start_recording(mission_name)
                except AlreadyRecordingError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)
            case _:
                raise NotImplementedError(f"Command {command} not implemented.")

        self.update_websocket()

    def set_replay_speed(self, speed: float):
        """Set the playback speed of the replay system."""
        try:
            speed = 0.0 if float(speed) < 0 else float(speed)
        except ValueError:
            speed = 0.0

        # Keeps last played speed updated while preventing it from hitting 0 if past speed is 0
        self.status.replay.last_played_speed = self.status.replay.speed if self.status.replay.speed != 0.0 else 1
        self.status.replay.speed = speed

        # Set replay status based on speed
        # If mission is not recorded, replay should be in DNE state.
        # if else, set to pause/playing based on speed
        if self.status.mission.state != MissionState.RECORDED:
            self.status.replay.state = ReplayState.DNE
        elif speed == 0.0:
            self.status.replay.state = ReplayState.PAUSED
            self.replay_input.put(f"speed {speed}")
        else:
            self.status.replay.state = ReplayState.PLAYING
            self.replay_input.put(f"speed {speed}")

    def stop_replay(self) -> None:
        """Stops the replay."""

        logger.info("REPLAY STOP")

        if self.replay is not None:
            self.replay.terminate()
        self.replay = None

        # Empty replay output
        self.replay_output: Queue[str] = mp.Queue()  # type:ignore
        self.reset_data()

    def play_mission(self, mission_name: str) -> None:
        """Plays the desired mission recording."""

        # Ensure not doing anything silly
        if self.status.mission.recording:
            raise AlreadyRecordingError

        mission_file = self.missions_dir.joinpath(f"{mission_name}.{MISSION_EXTENSION}")
        if mission_file not in self.status.replay.mission_files_list:
            raise MissionNotFoundError(mission_name)

        # Set output data to current mission
        self.status.mission.name = mission_name

        # We are not to record when replaying missions
        self.status.mission.state = MissionState.RECORDED
        self.status.mission.recording = False

        # Replay system
        if self.replay is None:
            self.replay = Process(
                target=TelemetryReplay(
                    self.replay_output,
                    self.replay_input,
                    self.status.replay.speed,
                    mission_file,
                ).run
            )
            self.replay.start()

        self.set_replay_speed(
            speed=self.status.replay.last_played_speed if self.status.replay.last_played_speed > 0 else 1
        )

        logger.info(f"REPLAY {mission_name} PLAYING")

    def start_recording(self, mission_name: str | None = None) -> None:
        """Starts recording the current mission. If no mission name is given, the recording epoch is used."""
        # TODO

    def stop_recording(self) -> None:
        """Stops the current recording."""

        logger.info("RECORDING STOP")
        # TODO

    def process_transmission(self, data: str) -> None:
        """Processes the incoming radio transmission data."""

        # Parse the transmission, if result is not null, update telemetry data
        parsed_transmission: ParsedTransmission | None = parse_rn2483_transmission(data, self.config)
        if parsed_transmission and parsed_transmission.blocks:
            # Updates the telemetry buffer with the latest block data and latest mission time
            self.telemetry_data.update_telemetry(parsed_transmission.packet_header.version, parsed_transmission.blocks)

            # TODO UPDATE FOR V1
            # Write data to file when recording
            # if self.status.mission.recording:
            #     logger.debug(f"Recording: {self.status.mission.recording}")
            #     self.mission_recording_buffer += TelemetryDataBlock(block.subtype, data=block).to_bytes()
            #     if len(self.mission_recording_buffer) >= 512:
            #         buffer_length = len(self.mission_recording_buffer)
            #         self.recording_write_bytes(buffer_length - (buffer_length % 512))
