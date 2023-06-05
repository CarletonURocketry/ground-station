# Telemetry to parse radio packets, keep history and to log everything
# Incoming information comes from rn2483_radio_payloads in payload format
# Outputs information to telemetry_json_output in friendly json for UI
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)
import logging
import math
from ast import literal_eval
from multiprocessing import Queue, Process, active_children
from pathlib import Path

# Imports
from signal import signal, SIGTERM
from struct import unpack
from time import time
from typing import Any

import modules.telemetry.json_packets as jsp
import modules.websocket.commands as wsc
from modules.telemetry.block import RadioBlockType, CommandBlockSubtype, ControlBlockSubtype
from modules.telemetry.data_block import DataBlock, DataBlockSubtype
from modules.telemetry.replay import TelemetryReplay
from modules.telemetry.sd_block import TelemetryDataBlock, LoggingMetadataSpacerBlock
from modules.telemetry.superblock import SuperBlock, Flight
from modules.misc.config import Config

# Types
BlockHeader = tuple[int, bool, int, int, int]
PacketHeader = tuple[str, int, int, int, int]

# Constants
ORG: str = "CUInSpace"
VERSION: str = "0.5.0-DEV"
MISSION_EXTENSION: str = "mission"
FILE_CREATION_ATTEMPT_LIMIT: int = 50

# Set up logging
logger = logging.getLogger(__name__)


# Helper functions
def mission_path(mission_name: str, missions_dir: Path, file_suffix: int = 0) -> Path:
    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}{'' if file_suffix == 0 else f'_{file_suffix}'}.{MISSION_EXTENSION}")


def shutdown_sequence() -> None:
    for child in active_children():
        child.terminate()
    exit(0)


def get_filepath_for_proposed_name(mission_name: str, missions_dir: Path) -> Path:
    """Obtains filepath for proposed name, with a maximum of giving a suffix 50 times before failing."""
    file_suffix = 1
    missions_filepath = mission_path(mission_name, missions_dir)

    while missions_filepath.is_file() and file_suffix < FILE_CREATION_ATTEMPT_LIMIT:
        missions_filepath = mission_path(mission_name, missions_dir, file_suffix)
        file_suffix += 1

    return missions_filepath


# Errors
class MissionNotFoundError(Exception):
    """Raised when the desired mission is not found."""

    def __init__(self, mission_name: str):
        self.mission_name = mission_name
        self.message = f"The mission recording '{mission_name}' does not exist."
        super().__init__(self.message)


class AlreadyRecordingError(Exception):
    """Raised if the telemetry process is already recording when instructed to record."""

    def __init__(self):
        self.message: str = "Recording is already in progress."
        super().__init__(self.message)


class ReplayPlaybackError(Exception):
    """Raised if the telemetry process replay system is active when instructed to record or recording."""

    def __init__(self):
        self.message: str = "Not recording when replay system is active."
        super().__init__(self.message)


# Main class
class Telemetry(Process):
    def __init__(
        self,
        serial_status: Queue,
        radio_payloads: Queue,
        rn2483_radio_input: Queue,
        radio_signal_report: Queue,
        telemetry_json_output: Queue,
        telemetry_ws_commands: Queue,
        config: Config,
    ):
        super().__init__()
        self.config = config

        self.radio_payloads = radio_payloads
        self.telemetry_json_output = telemetry_json_output
        self.telemetry_ws_commands = telemetry_ws_commands
        self.rn2483_radio_input = rn2483_radio_input
        self.radio_signal_report = radio_signal_report
        self.serial_status = serial_status

        # Telemetry Data holds a dict of the latest copy of received data blocks stored under the subtype name as a key.
        self.status: jsp.StatusData = jsp.StatusData()
        self.telemetry: dict = {}

        # Mission System
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path = None

        # Mission Recording
        self.mission_recording_file = None
        self.mission_recording_sb: SuperBlock = SuperBlock()
        self.mission_recording_buffer: bytearray = bytearray(b"")

        # Replay System
        self.replay = None
        self.replay_input = Queue()
        self.replay_output = Queue()

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)

        # Start Telemetry
        self.update_websocket()
        self.run()

    def run(self):
        while True:
            while not self.telemetry_ws_commands.empty():
                # Parse websocket command into an enum
                commands: list[str] = self.telemetry_ws_commands.get()
                command = wsc.parse(commands, wsc.WebsocketCommand)
                parameters = commands  # Remaining items in the commands list are parameters
                try:
                    self.execute_command(command, parameters)
                except AttributeError as e:
                    logger.error(e)

            while not self.radio_signal_report.empty():
                # TODO set radio SNR
                logger.info(f"SIGNAL DATA {self.radio_signal_report.get()}")

            while not self.serial_status.empty():
                x = self.serial_status.get().split(" ", maxsplit=1)
                self.parse_serial_status(command=x[0], data=x[1])
                self.update_websocket()

            # Switch data queues between replay and radio depending on mission state
            match self.status.mission.state:
                case jsp.MissionState.RECORDED:
                    while not self.replay_output.empty():
                        block_type, block_subtype, block_data = self.replay_output.get()
                        self.parse_rn2483_payload(block_type, block_subtype, block_data)
                        self.update_websocket()
                case _:
                    while not self.radio_payloads.empty():
                        self.parse_rn2483_transmission(self.radio_payloads.get())
                        self.update_websocket()

    def update_websocket(self) -> None:
        """Updates the websocket with the latest packet using the JSON output process."""
        self.telemetry_json_output.put(self.generate_websocket_response())

    def generate_websocket_response(self) -> dict[str, Any]:
        """Returns the dictionary containing the JSON data for the websocket client."""
        return {"version": VERSION, "org": ORG, "status": dict(self.status), "telemetry": self.telemetry}

    def reset_data(self) -> None:
        """Resets all live data on the telemetry backend to a default state."""
        self.status = jsp.StatusData()
        self.telemetry = {}

    def parse_serial_status(self, command: str, data: str):
        """Parses the serial managers status output"""
        match command:
            case "serial_ports":
                self.status.serial.available_ports = literal_eval(data)
            case "rn2483_connected":
                self.status.rn2483_radio.connected = bool(data)
            case "rn2483_port":
                if self.status.mission.state != jsp.MissionState.DNE:
                    self.reset_data()
                self.status.rn2483_radio.connected_port = data

                match self.status.rn2483_radio.connected_port:
                    case "":
                        self.status.mission.state = jsp.MissionState.DNE
                    case _:
                        self.status.mission.state = jsp.MissionState.LIVE

    def execute_command(self, command: wsc.Enum, parameters: list[str]) -> None:
        """Executes the passed websocket command."""

        WSCommand = wsc.WebsocketCommand
        match command:
            case WSCommand.UPDATE:
                self.status.replay.update_mission_list()

            # Replay commands
            case WSCommand.REPLAY.value.PLAY:
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.play_mission(mission_name)
                except MissionNotFoundError as e:
                    logger.error(e.message)
                except ReplayPlaybackError as e:
                    logger.error(e.message)

            case WSCommand.REPLAY.value.STOP:
                self.stop_replay()
            case WSCommand.REPLAY.value.PAUSE:
                self.set_replay_speed(0.0)
            case WSCommand.REPLAY.value.SPEED:
                self.set_replay_speed(float(parameters[0]))

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
        if self.status.mission.state != jsp.MissionState.RECORDED:
            self.status.replay.state = jsp.ReplayState.DNE
        elif speed == 0.0:
            self.status.replay.state = jsp.ReplayState.PAUSED
            self.replay_input.put(f"speed {speed}")
        else:
            self.status.replay.state = jsp.ReplayState.PLAYING
            self.replay_input.put(f"speed {speed}")

    def stop_replay(self) -> None:
        """Stops the replay."""

        logger.info("REPLAY STOP")

        if self.replay is not None:
            self.replay.terminate()
        self.replay = None

        self.reset_data()
        # Empty replay output
        self.replay_output = Queue()

    def play_mission(self, mission_name: str) -> None:
        """Plays the desired mission recording."""
        if self.status.mission.recording:
            raise ReplayPlaybackError

        mission_file = mission_path(mission_name, self.missions_dir)
        if mission_name is not None and mission_file not in self.status.replay.mission_files_list:
            raise MissionNotFoundError(mission_name)

        if self.replay is None:
            self.status.mission.name = mission_name
            self.status.mission.epoch = [
                mission["epoch"] for mission in self.status.replay.mission_list if mission["name"] == mission_name
            ][0]
            self.status.mission.state = jsp.MissionState.RECORDED
            self.status.mission.recording = False

            self.replay = Process(
                target=TelemetryReplay,
                args=(self.replay_output, self.replay_input, self.status.replay.speed, mission_file),
            )
            self.replay.start()

        self.set_replay_speed(
            speed=self.status.replay.last_played_speed if self.status.replay.last_played_speed > 0 else 1
        )
        logger.info(f"REPLAY {mission_name} PLAYING")

    def start_recording(self, mission_name: str = None) -> None:
        """Starts recording the current mission. If no mission name is given, the recording epoch is used."""

        # Do not record if already recording or if replay is active
        if self.status.mission.recording:
            raise AlreadyRecordingError
        if self.status.replay.state != jsp.ReplayState.DNE:
            raise ReplayPlaybackError

        logger.info("RECORDING START")

        # Mission Name
        recording_epoch = int(time())
        mission_name = str(recording_epoch) if not mission_name else mission_name
        self.mission_path = get_filepath_for_proposed_name(mission_name, self.missions_dir)
        self.mission_recording_file = open(self.mission_path, "wb")

        # Create SuperBlock in file
        flight = Flight(first_block=1, num_blocks=0, timestamp=recording_epoch)
        self.mission_recording_sb.flights = [flight]
        self.mission_recording_file.write(self.mission_recording_sb.to_bytes())
        self.mission_recording_file.flush()

        # Status update
        self.status.mission.name = mission_name
        self.status.mission.epoch = recording_epoch
        self.status.mission.recording = True

    def stop_recording(self) -> None:
        """Stops the current recording."""

        logger.info("RECORDING STOP")

        # Flush buffer and close off file
        self.recording_write_bytes(len(self.mission_recording_buffer), spacer=True)
        self.mission_recording_file.flush()
        self.mission_recording_file.close()

        # Reset recording data
        self.mission_recording_file = None
        self.mission_recording_sb = SuperBlock()
        self.mission_recording_buffer = bytearray(b"")

        # Reset mission data except state and last mission time
        self.status.mission = jsp.MissionData(
            state=self.status.mission.state, last_mission_time=self.status.mission.last_mission_time
        )

    def recording_write_bytes(self, num_bytes: int, spacer: bool = False) -> None:
        """Outputs the specified number of bytes from the buffer to the recording file"""

        # If the file is open
        if self.mission_recording_file is None:
            return

        # If there's nothing in buffer
        # Then there's no need to dump buffer
        if num_bytes == 0:
            return

        # Update Superblock with new block count
        self.mission_recording_sb.flights[0].num_blocks += int(math.ceil(num_bytes / 512))
        self.mission_recording_file.seek(0)
        self.mission_recording_file.write(self.mission_recording_sb.to_bytes())

        # Dump entire buffer to file
        blocks = self.mission_recording_buffer[:num_bytes]
        self.mission_recording_buffer = self.mission_recording_buffer[num_bytes:]
        self.mission_recording_file.seek(0, 2)
        self.mission_recording_file.write(blocks)

        # If less than 512 bytes, or a spacer is requested then write a spacer
        if num_bytes < 512 or spacer:
            spacer_block = LoggingMetadataSpacerBlock(512 - (num_bytes % 512))
            self.mission_recording_file.write(spacer_block.to_bytes())

    def parse_rn2483_payload(self, block_type: int, block_subtype: int, block_contents: str) -> None:
        """Parses telemetry payload blocks from either parsed packets or stored replays."""
        """ Block contents are a hex string. """

        # Working with hex strings until this point.
        # Hex/Bytes Demarcation point
        logger.debug(f"Block contents: {block_contents}")
        block_contents = bytes.fromhex(block_contents)
        try:
            radio_block = RadioBlockType(block_type)
        except Exception:
            logger.info(f"Received invalid radio block type of {block_type}.")
            return
        try:
            match radio_block:
                case RadioBlockType.CONTROL:
                    # CONTROL BLOCK DETECTED
                    logger.info(f"Control block received of subtype {ControlBlockSubtype(block_subtype)}")
                    # GOT SIGNAL REPORT (ONLY CONTROL BLOCK BEING USED CURRENTLY)
                    self.rn2483_radio_input.put("radio get snr")
                    # self.rn2483_radio_input.put("radio get rssi")
                    return
                case RadioBlockType.COMMAND:
                    # COMMAND BLOCK DETECTED
                    logger.info(f"Command block received of subtype {CommandBlockSubtype(block_subtype)}")
                    self.rn2483_radio_input.put("radio get snr")
                    return
                case RadioBlockType.DATA:
                    # DATA BLOCK DETECTED
                    block_data = DataBlock.parse(DataBlockSubtype(block_subtype), block_contents)
                    # Increase the last mission time
                    if block_data.mission_time > self.status.mission.last_mission_time:
                        self.status.mission.last_mission_time = block_data.mission_time

                    # Write data to file when recording
                    if self.status.mission.recording:
                        self.mission_recording_buffer += TelemetryDataBlock(data=block_data).to_bytes()
                        if len(self.mission_recording_buffer) >= 512:
                            buffer_length = len(self.mission_recording_buffer)
                            self.recording_write_bytes(buffer_length - (buffer_length % 512))

                    if block_subtype == DataBlockSubtype.STATUS:
                        self.status.rocket = jsp.RocketData.from_data_block(block_data)
                    else:
                        self.telemetry[DataBlockSubtype(block_subtype).name.lower()] = dict(block_data)
                case _:
                    logger.warning("Unknown block type.")
        except Exception as e:
            logger.error(f"Problem parsing RadioBlock: {e}")

    def parse_rn2483_transmission(self, data: str):
        """Parses RN2483 Packets and extracts our telemetry payload blocks"""

        # Extract the packet header
        data = data.strip()  # Sometimes some extra whitespace
        logger.debug(f"Full data string: {data}")
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])
        call_sign = call_sign.upper()  # Uppercase formatting because that's standard

        if length <= 24:  # If this packet nothing more than just the header
            logger.info(call_sign, length, version, srs_addr, packet_num)

        blocks = data[24:]  # Remove the packet header

        if call_sign in self.config.approved_callsigns:
            logger.info(f"Incoming packet from {call_sign} ({self.config.approved_callsigns.get(call_sign)})")
        else:
            logger.warning(f"Incoming packet from unauthorized callsign {call_sign}")

        # Parse through all blocks
        while blocks != "":
            # Parse block header
            logger.debug(f"Blocks: {blocks}")
            logger.debug(f"Block header: {blocks[:8]}")
            block_header = blocks[:8]
            block_len, crypto_signature, block_type, block_subtype, dest_addr = _parse_block_header(block_header)

            block_len = block_len * 2  # Convert length in bytes to length in hex symbols
            block_contents = blocks[8 : 8 + block_len]

            self.parse_rn2483_payload(block_type, block_subtype, block_contents)

            # Remove the data we processed from the whole set, and move onto the next data block
            blocks = blocks[8 + block_len :]


def _parse_packet_header(header: str) -> PacketHeader:
    """
    Returns the packet header string's informational components in a tuple.

    call_sign: str
    length: int
    version: int
    src_addr: int
    packet_num: int
    """

    # Extract call sign in utf-8
    logger.debug(f"Packet header: {header}")
    call_sign: str = bytes.fromhex(header[:12]).decode("utf-8")

    # Convert header from hex to binary
    header = bin(int(header, 16))[2:]

    # Extract values and then convert them to ints
    length: int = (int(header[47:53], 2) + 1) * 4
    version: int = int(header[53:58], 2)
    src_addr: int = int(header[63:67], 2)
    packet_num: int = int(header[67:79], 2)
    logger.debug(f"{length:=}, {version:=}, {src_addr:=}, {packet_num:=}")

    return call_sign, length, version, src_addr, packet_num


def _parse_block_header(header: str) -> BlockHeader:
    """
    Parses a block header string into its information components and returns them in a tuple.

    block_len: int
    crypto_signature: bool
    message_type: int
    message_subtype: int
    destination_addr: int
    """
    bits_header = bin(int(header, 16))[2:]  # Convert header to binary
    logger.debug(f"Block header {header} -> {bits_header}")

    block_len = (int(bits_header[:5], 2) + 1) * 4  # Length of the data block
    crypto_signature = int(bits_header[5], 2)
    message_type = int(bits_header[6:10], 2)  # 0 - Control, 1 - Command, 2 - Data
    message_subtype = int(bits_header[10:16], 2)
    destination_addr = int(bits_header[16:20], 2)  # 0 - GStation, 1 - Rocket

    int_header = unpack("<I", bytes.fromhex(header))[0]
    block_len = ((int_header & 0x1F) + 1) * 4
    crypto_signature = bool((int_header >> 5) & 0x1)
    message_type = (int_header >> 6) & 0xF
    message_subtype = (int_header >> 10) & 0x3F
    destination_addr = (int_header >> 16) & 0xF
    logger.debug(f"{block_len:=}, {crypto_signature:=}, {message_type:=}, {message_subtype:=}, {destination_addr:=}")

    return block_len, crypto_signature, message_type, message_subtype, destination_addr
