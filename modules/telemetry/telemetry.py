# Telemetry to parse radio packets, keep history and to log everything
# Incoming information comes from rn2483_radio_payloads in payload format
# Outputs information to telemetry_json_output in friendly json for UI
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)

# Imports
import time
from struct import unpack
from time import sleep, time
from pathlib import Path
from multiprocessing import Queue, Process, Value
from multiprocessing.shared_memory import ShareableList

from modules.telemetry.block import BlockTypes
from modules.telemetry.data_block import DataBlock, DataBlockSubtype
from modules.telemetry.replay import TelemetryReplay

import modules.telemetry.json_packets as jsp
import modules.websocket.commands as wsc

# Types
BlockHeader = tuple[int, bool, int, int, int]
PacketHeader = tuple[str, int, int, int, int]

# Constants
ORG: str = "CUInSpace"
VERSION: str = "0.4.4-DEV"
REPLAY_STATE: int = 1
MISSION_EXTENSION: str = ".mission"
FILE_CREATION_ATTEMPT_LIMIT: int = 50


# Helper functions
def mission_path(mission_name: str, missions_dir: Path) -> Path:

    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}{MISSION_EXTENSION}")


def get_filepath_for_proposed_name(mission_name: str, missions_dir: Path) -> Path:

    missions_filepath = missions_dir.joinpath(f"{mission_name}{MISSION_EXTENSION}")
    file_suffix = 1

    while missions_filepath.is_file() and file_suffix < FILE_CREATION_ATTEMPT_LIMIT:
        missions_filepath = missions_dir.joinpath(f"{mission_name}_{file_suffix}{MISSION_EXTENSION}")
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
    def __init__(self, serial_connected: Value, serial_connected_port: Value, serial_ports: ShareableList,
                 radio_payloads: Queue, telemetry_json_output: Queue, telemetry_ws_commands: Queue,
                 serial_status: Queue):
        super().__init__()

        self.radio_payloads = radio_payloads
        self.telemetry_json_output = telemetry_json_output
        self.telemetry_ws_commands = telemetry_ws_commands

        self.serial_ports = serial_ports
        self.serial_connected = serial_connected
        self.serial_connected_port = serial_connected_port
        self.serial_status = serial_status

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
                self.execute_command(command, parameters)

            while not self.serial_status.empty():
                print(self.serial_status.get())

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

            if bool(self.serial_connected.value) != self.status_data.rn3483_radio.connected:
                self.reset_data()

                match self.serial_connected_port[0]:
                    case "test":
                        self.status_data.mission.state = jsp.MissionState.TEST
                    case "":
                        self.status_data.mission.state = jsp.MissionState.DNE
                    case _:
                        self.status_data.mission.state = jsp.MissionState.LIVE
                self.update_websocket()

            sleep(0.2)

    def update_websocket(self) -> None:

        """Updates the mission replay list and puts the latest packet on the JSON output process."""

        self.replay_data.update_mission_list()
        self.telemetry_json_output.put(self.generate_websocket_response())

    def shareable_to_list(self, empty_padding=True) -> list:
        new_list = [""]

        try:
            new_list = [""] * len(self.serial_ports)

            for i in range(len(self.serial_ports)):
                new_list[i] = str(self.serial_ports[i])

            if empty_padding:
                new_list = ' '.join(new_list).split()

        except TypeError:
            print(f"{new_list}")

        return new_list

    def reset_data(self):
        self.status_data = jsp.StatusData()
        self.telemetry_data = {}
        self.replay_data = jsp.ReplayData()

        self.status_data.serial.available_ports = self.shareable_to_list()

    def generate_websocket_response(self, telemetry_keys="all"):
        return {"version": VERSION, "org": ORG,
                "status": dict(self.generate_status_data()),
                "telemetry_data": self.generate_telemetry_data(telemetry_keys),
                "replay": dict(self.replay_data)}

    def generate_status_data(self):
        self.status_data.rn3483_radio.connected = bool(self.serial_connected.value)
        self.status_data.rn3483_radio.connected_port = self.serial_connected_port[0]
        self.status_data.serial.available_ports = self.shareable_to_list()

        return self.status_data

    def generate_telemetry_data(self, keys_to_send="all"):
        if keys_to_send == "all":
            keys_to_send = self.telemetry_data.keys()

        telemetry_data_block = {}
        for key in keys_to_send:
            if key in self.telemetry_data.keys():
                telemetry_data_block[key] = self.telemetry_data[key]

        return telemetry_data_block

    def execute_command(self, command: wsc.Enum, parameters: list[str]) -> None:
        
        """Executes the passed websocket command."""

        match command:
            case wsc.WebsocketCommand.UPDATE:
                self.update_websocket()

            # Replay commands
            case wsc.WebsocketCommand.REPLAY.PLAY:
                mission_name = " ".join(parameters)
                try:
                    self.play_mission(mission_name)
                except MissionNotFoundError as e:
                    print(e.message)
                else:
                    self.update_websocket()
            case wsc.WebsocketCommand.REPLAY.STOP:
                self.stop_replay()
                self.update_websocket()
            case wsc.WebsocketCommand.REPLAY.PAUSE:
                self.set_replay_speed(0.0)
                self.update_websocket()
            case wsc.WebsocketCommand.REPLAY.SPEED:
                self.set_replay_speed(int(parameters[0]))
                self.update_websocket()

            # Record commands
            case wsc.WebsocketCommand.RECORD.STOP:
                self.stop_recording()
            case wsc.WebsocketCommand.RECORD.START:
                # If there is no mission name, use the default
                mission_name = None if not parameters else " ".join(parameters)
                try:
                    self.start_recording(mission_name)
                except AlreadyRecordingError as e:
                    print(e.message)

    def set_replay_speed(self, speed: float):

        """Set the playback speed of the replay system."""

        speed = 0.0 if speed < 0 else speed

        if speed == 0.0:
            self.replay_data.status = jsp.ReplayState.PAUSED

        self.replay_data.status = jsp.ReplayState.PLAYING
        self.replay_input.put(f"speed {speed}")

    def stop_replay(self) -> None:

        """Stops the replay."""

        print("REPLAY STOP")
        self.replay.terminate()
        self.replay = None

        self.reset_data()
        while not self.replay_output.empty():
            self.replay_output.get()

    def play_mission(self, mission_name: str) -> None:

        """Plays the desired mission recording."""

        if mission_name not in self.replay_data.mission_list:
            raise MissionNotFoundError(mission_name)

        self.status_data.mission.name = mission_name
        replay_mission_filepath = mission_path(mission_name, self.missions_dir)

        if self.replay is None:
            self.replay = Process(
                target=TelemetryReplay,
                args=(
                    self.replay_output,
                    self.replay_input,
                    replay_mission_filepath
                )
            )
            self.replay.start()

        self.set_replay_speed(speed=1)
        self.status_data.mission.state = jsp.MissionState.RECORDED
        print(f"REPLAY {mission_name} PLAYING")

    def start_recording(self, mission_name: str = None) -> None:

        """Starts recording the current mission. If no mission name is give, the recording epoch is used."""

        if self.status_data.mission.recording:
            raise AlreadyRecordingError

        print("RECORDING START")

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

        print("RECORDING STOP")
        self.status_data.mission = jsp.MissionData(state=self.status_data.mission.state)

    def parse_rn2483_payload(self, block_type: int, block_subtype: int, block_contents):
        # Working with hex strings until this point.
        # Hex/Bytes Demarcation point
        block_contents = bytes.fromhex(block_contents)
        match BlockTypes(block_type):
            case BlockTypes.CONTROL:
                # CONTROL BLOCK DETECTED
                # TODO Make a separate serial output just for signal data
                print("CONTROL BLOCK")
                self.replay_input.put("radio get snr")
                # snr = self._read_ser();
                self.replay_input.put("radio get rssi")
                # rssi = self._read_ser()
            case BlockTypes.COMMAND:
                # COMMAND BLOCK DETECTED
                print("Command block")
            case BlockTypes.DATA:
                # DATA BLOCK DETECTED
                block_data = DataBlock.parse(DataBlockSubtype(block_subtype), block_contents)
                print(block_data)
                # Increase the last mission time
                if block_data.mission_time > self.status_data.rocket.last_mission_time:
                    self.status_data.rocket.last_mission_time = block_data.mission_time

                # Move status telemetry block to the status key instead of under telemetry
                if DataBlockSubtype(block_subtype) == DataBlockSubtype.STATUS:
                    self.status_data.rocket = jsp.RocketData.from_data_block(block_data)
                else:
                    self.telemetry_data[DataBlockSubtype(block_subtype).name.lower()] = dict(block_data)
            case _:
                print("Unknown block type")

    def parse_rn2483_transmission(self, data: str):

        # Extract the packet header
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

        if length <= 24:  # If this packet nothing more than just the header
            print(call_sign, length, version, srs_addr, packet_num)

        blocks = data[24:]  # Remove the packet header

        print("-----" * 20)
        # print(f'{DeviceAddress(srs_addr)} - {call_sign} - sent you a packet:')
        print(f"{call_sign} - sent you a packet")

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
        print(f"-----" * 20)


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


def make_block_header():
    header = "840C0000"

    # block_len = ((header[0] & 0x1f) + 1) * 4  # Length of the data block
    # crypto_signature = ((header[0] >> 5) & 0x1)
    # message_type = ((header[0] >> 6) & 0xf)  # 0 - Control, 1 - Command, 2 - Data
    # message_subtype = ((header[0] >> 10) & 0x3f)
    # destination_addr = ((header[0] >> 16) & 0xf)  # 0 - GStation, 1 - Rocket

    # lol = "13634180"
    # header = struct.pack('<I', lol)
    # print("HEADDDDDDDDD",header)
    # lol = 13634180
    # header = struct.pack('<I', lol)
    # print("HEADDDDDDDDD", int.from_bytes(header, "little"))

    # test = struct.pack('<I?III', 20, False, 2, 3, 0)
    # print("LLLLLLLL",test.hex())
    return header
