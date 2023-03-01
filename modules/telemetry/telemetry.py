# Telemetry to parse radio packets, keep history and to log everything
# Incoming information comes from rn2483_radio_payloads in payload format
# Outputs information to telemetry_json_output in friendly json for UI
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)

# Imports
from signal import signal, SIGTERM
from struct import unpack
from time import time
from pathlib import Path
from ast import literal_eval
from typing import Any
import logging

from multiprocessing import Queue, Process, active_children
from modules.telemetry.replay import TelemetryReplay
from modules.telemetry.block import BlockTypes
from modules.telemetry.data_block import DataBlock, DataBlockSubtype

import modules.telemetry.json_packets as jsp
import modules.websocket.commands as wsc

# Types
BlockHeader = tuple[int, bool, int, int, int]
PacketHeader = tuple[str, int, int, int, int]

# Constants
ORG: str = "CUInSpace"
VERSION: str = "0.4.5-DEV"
MISSION_EXTENSION: str = "mission"
FILE_CREATION_ATTEMPT_LIMIT: int = 50


# Helper functions
def mission_path(mission_name: str, missions_dir: Path) -> Path:
    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}.{MISSION_EXTENSION}")


def shutdown_sequence() -> None:
    for child in active_children():
        child.terminate()
    exit(0)


def get_filepath_for_proposed_name(mission_name: str, missions_dir: Path) -> Path:
    """Obtains filepath for proposed name, with a maximum of giving a suffix 50 times before failing."""
    file_suffix = 1
    missions_filepath = missions_dir.joinpath(f"{mission_name}.{MISSION_EXTENSION}")

    while missions_filepath.is_file() and file_suffix < FILE_CREATION_ATTEMPT_LIMIT:
        missions_filepath = missions_dir.joinpath(f"{mission_name}_{file_suffix}.{MISSION_EXTENSION}")
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


# Main class
class Telemetry(Process):
    def __init__(self, serial_status: Queue, radio_payloads: Queue, rn2483_radio_input: Queue,
                 radio_signal_report: Queue, telemetry_json_output: Queue, telemetry_ws_commands: Queue):
        super().__init__()

        self.radio_payloads = radio_payloads
        self.telemetry_json_output = telemetry_json_output
        self.telemetry_ws_commands = telemetry_ws_commands
        self.rn2483_radio_input = rn2483_radio_input
        self.radio_signal_report = radio_signal_report

        self.serial_status = serial_status
        self.serial_ports = []

        # Telemetry Data holds a dict of the latest copy of received data blocks stored under the subtype name as a key.
        self.status_data: jsp.StatusData = jsp.StatusData()
        self.telemetry_data = {}
        self.replay_data = jsp.ReplayData()

        # Mission Path
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path = None

        # Replay System
        self.replay = None
        self.replay_input = Queue()
        self.replay_output = Queue()
        self.replay_last_played_speed = 1

        # Handle program closing to ensure no orphan processes
        signal(SIGTERM, shutdown_sequence)

        # Start Telemetry
        self.reset_data()
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
                    logging.error(e)

            while not self.radio_signal_report.empty():
                logging.info("SIGNAL DATA", self.radio_signal_report.get())

            while not self.serial_status.empty():
                x = self.serial_status.get().split(" ", maxsplit=1)

                match x[0]:
                    case "serial_ports":
                        self.serial_ports = literal_eval(x[1])
                        self.status_data.serial.available_ports = self.serial_ports
                    case "rn2483_connected":
                        self.status_data.rn2483_radio.connected = bool(x[1])
                    case "rn2483_port":
                        self.reset_data()
                        self.status_data.rn2483_radio.connected_port = x[1]

                        match self.status_data.rn2483_radio.connected_port:
                            case "test":
                                self.status_data.mission.state = jsp.MissionState.TEST
                            case "":
                                self.status_data.mission.state = jsp.MissionState.DNE
                            case _:
                                self.status_data.mission.state = jsp.MissionState.LIVE

                self.update_websocket()

            match self.status_data.mission.state:
                case jsp.MissionState.RECORDED:
                    # REPLAY SYSTEM
                    while not self.replay_output.empty():
                        block_type, block_subtype, block_data = self.replay_output.get()
                        self.parse_rn2483_payload(block_type, block_subtype, block_data)
                        self.update_websocket()
                case _:
                    # RADIO PAYLOADS
                    while not self.radio_payloads.empty():
                        self.parse_rn2483_transmission(self.radio_payloads.get())
                        self.update_websocket()

    def update_websocket(self) -> None:
        """Updates the websocket with the latest packet using the JSON output process."""

        self.telemetry_json_output.put(self.generate_websocket_response())

    def reset_data(self) -> None:
        """Resets all live data on the telemetry backend to a default state."""
        self.status_data = jsp.StatusData()
        self.telemetry_data = {}
        self.replay_data = jsp.ReplayData()

    def generate_websocket_response(self) -> dict[str, Any]:
        """Returns the dictionary containing the JSON data for the websocket client."""

        return {"version": VERSION, "org": ORG,
                "status": dict(self.status_data),
                "telemetry": self.telemetry_data,
                "replay": dict(self.replay_data)}

    def execute_command(self, command: wsc.Enum, parameters: list[str]) -> None:
        """Executes the passed websocket command."""

        match command:
            case wsc.WebsocketCommand.UPDATE:
                self.replay_data.update_mission_list()

            # Replay commands
            case wsc.WebsocketCommand.REPLAY.value.PLAY:
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.play_mission(mission_name)
                except MissionNotFoundError as e:
                    logging.error(e.message)

            case wsc.WebsocketCommand.REPLAY.value.STOP:
                self.replay_last_played_speed = self.replay_data.speed
                self.stop_replay()
            case wsc.WebsocketCommand.REPLAY.value.PAUSE:
                self.replay_last_played_speed = self.replay_data.speed
                self.set_replay_speed(0.0)
            case wsc.WebsocketCommand.REPLAY.value.SPEED:
                self.set_replay_speed(int(parameters[0]))

            # Record commands
            case wsc.WebsocketCommand.RECORD.value.STOP:
                self.stop_recording()
            case wsc.WebsocketCommand.RECORD.value.START:
                # If there is no mission name, use the default
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.start_recording(mission_name)
                except AlreadyRecordingError as e:
                    logging.error(e.message)

        self.update_websocket()

    def set_replay_speed(self, speed: float):
        """Set the playback speed of the replay system."""
        try:
            speed = 0.0 if float(speed) < 0 else float(speed)
        except ValueError:
            speed = 0.0

        if speed == 0.0:
            self.replay_data.status = jsp.ReplayState.PAUSED
        else:
            self.replay_data.status = jsp.ReplayState.PLAYING

        self.replay_data.speed = speed
        self.replay_input.put(f"speed {speed}")

    def stop_replay(self) -> None:
        """Stops the replay."""

        logging.info("REPLAY STOP")

        if self.replay is not None:
            self.replay.join()
        self.replay = None

        self.reset_data()
        # Empty replay output
        while not self.replay_output.empty():
            self.replay_output.get()

    def play_mission(self, mission_name: str) -> None:
        """Plays the desired mission recording."""

        if mission_name not in self.replay_data.mission_list and mission_name is not None:
            raise MissionNotFoundError(mission_name)

        if self.replay is None:
            self.status_data.mission.name = mission_name
            self.status_data.mission.state = jsp.MissionState.RECORDED
            replay_mission_filepath = mission_path(mission_name, self.missions_dir)

            self.replay = Process(
                target=TelemetryReplay,
                args=(
                    self.replay_output,
                    self.replay_input,
                    replay_mission_filepath
                )
            )
            self.replay.start()

        self.set_replay_speed(speed=self.replay_last_played_speed if self.replay_last_played_speed > 0 else 1)
        logging.info(f"REPLAY {mission_name} PLAYING")

    def start_recording(self, mission_name: str = None) -> None:
        """Starts recording the current mission. If no mission name is given, the recording epoch is used."""

        if self.status_data.mission.recording:
            raise AlreadyRecordingError

        logging.info("RECORDING START")

        recording_epoch = int(time())
        mission_name = str(recording_epoch) if not mission_name else mission_name
        self.mission_path = get_filepath_for_proposed_name(mission_name, self.missions_dir)
        self.mission_path.write_text(f"{1},{recording_epoch}\n")

        self.status_data.mission.name = mission_name
        self.status_data.mission.epoch = recording_epoch
        self.status_data.mission.recording = True

        self.replay_data.update_mission_list()

    def stop_recording(self) -> None:
        """Stops the current recording."""

        logging.info("RECORDING STOP")
        self.status_data.mission.recording = False
        self.status_data.mission = jsp.MissionData(state=self.status_data.mission.state)

    def parse_rn2483_payload(self, block_type: int, block_subtype: int, block_contents: str) -> None:
        """ Parses telemetry payload blocks from either parsed packets or stored replays. """
        """ Block contents are a hex string. """

        # Working with hex strings until this point.
        # Hex/Bytes Demarcation point
        block_contents = bytes.fromhex(block_contents)
        match BlockTypes(block_type):
            case BlockTypes.CONTROL:
                # CONTROL BLOCK DETECTED
                logging.info("CONTROL BLOCK")
                # GOT SIGNAL REPORT (ONLY CONTROL BLOCK BEING USED CURRENTLY)
                self.rn2483_radio_input.put("radio get snr")
                # self.rn2483_radio_input.put("radio get rssi")

            case BlockTypes.COMMAND:
                # COMMAND BLOCK DETECTED
                logging.info("Command block")
            case BlockTypes.DATA:
                # DATA BLOCK DETECTED
                block_data = DataBlock.parse(DataBlockSubtype(block_subtype), block_contents)
                logging.info(block_data)
                # Increase the last mission time
                if block_data.mission_time > self.status_data.rocket.last_mission_time:
                    self.status_data.rocket.last_mission_time = block_data.mission_time

                if block_subtype == DataBlockSubtype.STATUS:
                    self.status_data.rocket = jsp.RocketData.from_data_block(block_data)
                else:
                    self.telemetry_data[DataBlockSubtype(block_subtype).name.lower()] = dict(block_data)
            case _:
                logging.warning("Unknown block type")

    def parse_rn2483_transmission(self, data: str):
        """ Parses RN2483 Packets and extracts our telemetry payload blocks"""
        # Extract the packet header
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

        if length <= 24:  # If this packet nothing more than just the header
            logging.info(call_sign, length, version, srs_addr, packet_num)

        blocks = data[24:]  # Remove the packet header

        logging.info(f"{call_sign} - sent you a packet")

        # Parse through all blocks
        while blocks != '':
            # Parse block header
            block_header = blocks[:8]
            block_len, crypto_signature, block_type, block_subtype, dest_addr = _parse_block_header(block_header)

            block_len = block_len * 2  # Convert length in bytes to length in hex symbols
            block_contents = blocks[8: 8 + block_len]

            if self.status_data.mission.recording:
                with open(f'{self.mission_path}', 'a') as mission:
                    mission.write(f"{block_type},{block_subtype},{block_contents}\n")

            self.parse_rn2483_payload(block_type, block_subtype, block_contents)

            # Remove the data we processed from the whole set, and move onto the next data block
            blocks = blocks[8 + block_len:]


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
    call_sign: str = bytes.fromhex(header[0:12]).decode("utf-8")

    # Convert header from hex to binary
    header = bin(int(header, 16))

    # Extract values and then convert them to ints
    length: int = (int(header[47:53], 2) + 1) * 4
    version: int = int(header[53:58], 2)
    src_addr: int = int(header[63:67], 2)
    packet_num: int = int(header[67:79], 2)

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
    header = unpack('<I', bytes.fromhex(header))

    block_len = ((header[0] & 0x1f) + 1) * 4  # Length of the data block
    crypto_signature = bool((header[0] >> 5) & 0x1)
    message_type = ((header[0] >> 6) & 0xf)  # 0 - Control, 1 - Command, 2 - Data
    message_subtype = ((header[0] >> 10) & 0x3f)
    destination_addr = ((header[0] >> 16) & 0xf)  # 0 - GStation, 1 - Rocket

    return block_len, crypto_signature, message_type, message_subtype, destination_addr
