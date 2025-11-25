"""
Telemetry to parse radio packets, keep history and to log everything.
Incoming information comes from rn2483_radio_payloads in payload format.
Outputs information to telemetry_json_output in friendly JSON for UI.
"""

from io import BufferedWriter, TextIOWrapper
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

from ground_station.telemetry.data import TelemetryBuffer
from ground_station.telemetry.status import TelemetryStatus, MissionState, ReplayState
import ground_station.telemetry.websocket_commands as wsc
from ground_station.misc.config import Config
from ground_station.telemetry.replay import TelemetryReplay
from ground_station.telemetry.parsing_utils import parse_rn2483_transmission, ParsedTransmission
from ground_station.telemetry.errors import MissionNotFoundError, AlreadyRecordingError, ReplayPlaybackError

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
        self.telemetry_data: TelemetryBuffer = TelemetryBuffer(self.config.telemetry_buffer_size)

        # Mission File System
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path: Path | None = None

        # Mission Recording
        self.mission_recording_file: TextIOWrapper[BufferedWriter] | None = None

        # Replay System
        self.replays: dict[str, Process] = {}  # client_id -> Process
        self.replay_inputs: dict[str, Queue[str]] = {}  # client_id -> input queue
        self.replay_outputs: dict[str, Queue[str]] = {}  # client_id -> output queue
        self.replay_telemetry_data: dict[str, TelemetryBuffer] = {}  # client_id -> per-client telemetry buffer

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
                    # Extract client_id from the first element (may be empty string)
                    client_id = commands.pop(0) if commands else ""
                    command = wsc.parse(commands, wsc.WebsocketCommand)
                    parameters = commands  # Remaining items in the commands list are parameters
                    self.execute_command(command, parameters, client_id)
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

            # Process replay outputs for each active replay client
            for client_id, replay_output in list(self.replay_outputs.items()):
                # Safety check: skip if this client's replay was stopped during iteration
                if client_id not in self.replay_outputs:
                    continue
                while not replay_output.empty():
                    # Process replay data into per-client buffer, not shared buffer
                    self.process_transmission(replay_output.get(), replay_client_id=client_id)
                    # Send replay data only to the specific client
                    self.update_websocket(target=client_id)

            # Process live radio data (send to all clients)
            while not self.rn2483_radio_payloads.empty():
                self.process_transmission(self.rn2483_radio_payloads.get())
                # Send live data to all clients
                self.update_websocket()

    def update_websocket(self, target: str | None = None) -> None:
        """Updates the websocket with the latest packet using the JSON output process.
        
        Args:
            target: Optional client ID to send the message to. If None or empty, sends to all clients.
        """
        # Treat empty string same as None for broadcasting
        if target == "":
            target = None
            
        # Use per-client buffer if this is for a replay client, otherwise use shared buffer
        telemetry_data = self.replay_telemetry_data.get(target, self.telemetry_data) if target else self.telemetry_data
        
        websocket_response = {
            "org": self.config.organization,
            "rocket": self.config.rocket_name,
            "version": self.version,
            "status": dict(self.status),
            "telemetry": telemetry_data.get(),
            "target": target,
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

    def execute_command(self, command: wsc.Enum, parameters: list[str], client_id: str = "") -> None:
        """Executes the passed websocket command.
        
        Args:
            command: The parsed websocket command enum.
            parameters: Additional parameters for the command.
            client_id: The ID of the client that sent the command (for replay targeting).
        """

        WSCommand = wsc.WebsocketCommand
        match command:
            case WSCommand.UPDATE:
                self.status.replay.update_mission_list()

            # Replay commands
            case WSCommand.REPLAY.value.PLAY:
                if not parameters:
                    raise ReplayPlaybackError
                if not client_id:
                    logger.error("Replay commands require a valid client_id")
                    return
                mission_name = " ".join(parameters)
                try:
                    self.play_mission(mission_name, client_id)
                except MissionNotFoundError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)
                # Update only the specific client for replay commands
                self.update_websocket(target=client_id)
                return  # Don't broadcast to all clients
            case WSCommand.REPLAY.value.PAUSE:
                if not client_id:
                    logger.error("Replay commands require a valid client_id")
                    return
                self.set_replay_speed(0.0, client_id)
                self.update_websocket(target=client_id)
                return
            case WSCommand.REPLAY.value.RESUME:
                if not client_id:
                    logger.error("Replay commands require a valid client_id")
                    return
                self.set_replay_speed(self.status.replay.last_played_speed, client_id)
                self.update_websocket(target=client_id)
                return
            case WSCommand.REPLAY.value.SPEED:
                if not client_id:
                    logger.error("Replay commands require a valid client_id")
                    return
                self.set_replay_speed(float(parameters[0]), client_id)
                self.update_websocket(target=client_id)
                return
            case WSCommand.REPLAY.value.STOP:
                if not client_id:
                    logger.error("Replay commands require a valid client_id")
                    return
                self.stop_replay(client_id)
                self.update_websocket(target=client_id)
                return

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

    def set_replay_speed(self, speed: float, client_id: str):
        """Set the playback speed of the replay system for a specific client."""
        try:
            speed = 0.0 if float(speed) < 0 else float(speed)
        except ValueError:
            speed = 0.0

        # Keeps last played speed updated while preventing it from hitting 0 if past speed is 0
        self.status.replay.last_played_speed = self.status.replay.speed if self.status.replay.speed != 0.0 else 1
        self.status.replay.speed = speed

        # Set replay status based on speed
        # If there are no active replays, replay should be in DNE state.
        # if else, set to pause/playing based on speed
        if not self.replays:
            self.status.replay.state = ReplayState.DNE
        elif speed == 0.0:
            self.status.replay.state = ReplayState.PAUSED
            if client_id in self.replay_inputs:
                self.replay_inputs[client_id].put(f"speed {speed}")
        else:
            self.status.replay.state = ReplayState.PLAYING
            if client_id in self.replay_inputs:
                self.replay_inputs[client_id].put(f"speed {speed}")

        logger.info(f"REPLAY SPEED {speed} for client {client_id}")

    def stop_replay(self, client_id: str | None = None) -> None:
        """Stops the replay for a specific client, or all replays if client_id is None."""

        if client_id:
            # Stop specific client's replay
            logger.info(f"REPLAY STOP for client {client_id}")
            if client_id in self.replays:
                self.replays[client_id].terminate()
                del self.replays[client_id]
            if client_id in self.replay_inputs:
                # Flush and delete input queue
                while not self.replay_inputs[client_id].empty():
                    self.replay_inputs[client_id].get()
                del self.replay_inputs[client_id]
            if client_id in self.replay_outputs:
                # Flush and delete output queue to prevent old packets from being processed
                while not self.replay_outputs[client_id].empty():
                    self.replay_outputs[client_id].get()
                del self.replay_outputs[client_id]
            if client_id in self.replay_telemetry_data:
                # Clean up per-client telemetry buffer
                del self.replay_telemetry_data[client_id]
        else:
            # Stop all replays
            logger.info("REPLAY STOP ALL")
            for replay_process in self.replays.values():
                replay_process.terminate()
            # Flush all queues
            for queue in self.replay_inputs.values():
                while not queue.empty():
                    queue.get()
            for queue in self.replay_outputs.values():
                while not queue.empty():
                    queue.get()
            self.replays.clear()
            self.replay_inputs.clear()
            self.replay_outputs.clear()
            self.replay_telemetry_data.clear()
            self.reset_data()

    def play_mission(self, mission_name: str, client_id: str) -> None:
        """Plays the desired mission recording for a specific client."""

        # Ensure not doing anything silly
        if self.status.mission.recording:
            raise AlreadyRecordingError

        mission_file = self.missions_dir.joinpath(f"{mission_name}.{MISSION_EXTENSION}")
        if mission_file not in self.status.replay.mission_files_list:
            raise MissionNotFoundError(mission_name)

        # Stop any existing replay for this client
        if client_id in self.replays:
            self.stop_replay(client_id)

        # Create new queues for this client's replay
        self.replay_inputs[client_id] = mp.Queue()  # type:ignore
        self.replay_outputs[client_id] = mp.Queue()  # type:ignore
        # Create per-client telemetry buffer for this replay
        self.replay_telemetry_data[client_id] = TelemetryBuffer(self.config.telemetry_buffer_size)

        # Create and start replay process for this client
        self.replays[client_id] = Process(
            target=TelemetryReplay(
                self.replay_outputs[client_id],
                self.replay_inputs[client_id],
                self.status.replay.speed,
                mission_file,
            ).run
        )
        self.replays[client_id].start()

        self.set_replay_speed(
            speed=self.status.replay.last_played_speed if self.status.replay.last_played_speed > 0 else 1,
            client_id=client_id,
        )

        logger.info(f"REPLAY {mission_name} PLAYING for client {client_id}")

    def start_recording(self, mission_name: str | None = None) -> None:
        """Starts recording the current mission. If no mission name is given, the recording epoch is used."""
        # TODO
        self.status.mission.recording = True
        self.mission_path = self.missions_dir.joinpath(f"{mission_name or 'default'}.{MISSION_EXTENSION}")
        # This long line creates a BufferedWriter object that can write plaintext
        self.mission_recording_file = TextIOWrapper(
            BufferedWriter(open(self.mission_path, "wb+", 0)), line_buffering=False, write_through=True
        )
        logger.info(f"Starting to record to {self.mission_path}")

    def stop_recording(self) -> None:
        """Stops the current recording."""

        self.status.mission.recording = False
        if self.mission_recording_file:
            self.mission_recording_file.close()
        self.mission_recording_file = None
        logger.info("Recording stopped")
        # TODO

    def process_transmission(self, data: str, replay_client_id: str | None = None) -> None:
        """Processes the incoming radio transmission data.
        
        Args:
            data: The transmission data to process
            replay_client_id: If provided, updates the per-client replay buffer instead of shared buffer
        """
        # Always write data to file when recording, even if it can't be parsed correctly
        if self.status.mission.recording and self.mission_recording_file:
            logger.info(f"Recording: {data}")
            self.mission_recording_file.write(f"{data}\n")

        try:
            # Parse the transmission, if result is not null, update telemetry data
            parsed: ParsedTransmission | None = parse_rn2483_transmission(data, self.config)
            if parsed and parsed.blocks:
                # Update the appropriate buffer: per-client for replay, shared for live data
                if replay_client_id and replay_client_id in self.replay_telemetry_data:
                    self.replay_telemetry_data[replay_client_id].add(parsed.blocks)
                else:
                    self.telemetry_data.add(parsed.blocks)
        except Exception as e:
            print(e)
            logger.error(e)
