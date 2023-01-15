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
from modules.telemetry.status_data import MissionState, StatusData, MissionData, RocketData

import modules.websocket.commands as wsc

# Constants
ORG: str = "CUInSpace"
VERSION: str = "0.4.4-DEV"
REPLAY_STATE: int = 1
MISSION_EXTENSION: str = ".mission"


# Helper functions
def mission_path(mission_name: str, missions_dir: Path) -> Path:

    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}{MISSION_EXTENSION}")


def get_mission_list(missions_dir: Path) -> list[str]:

    """Returns a list of the available mission recordings in the missions directory."""

    return [name.stem for name in missions_dir.glob(f"*{MISSION_EXTENSION}") if name.is_file()]


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
        self.status_data: StatusData = StatusData()
        self.telemetry_data = {}
        self.replay_data = {}

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
                parameters = commands
                self.execute_command(command, parameters)

                self.parse_ws_commands(self.telemetry_ws_commands.get())

            while not self.serial_status.empty():
                print(self.serial_status.get())

            match self.status_data.mission.state:
                case MissionState.RECORDED:
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
                        self.status_data.mission.state = MissionState.TEST
                    case "":
                        self.status_data.mission.state = MissionState.DNE
                    case _:
                        self.status_data.mission.state = MissionState.LIVE
                self.update_websocket()

            sleep(0.2)

    def update_websocket(self) -> None:

        """Updates the mission replay list and puts the latest packet on the JSON output process."""

        self.replay_data["mission_list"] = get_mission_list(self.missions_dir)
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
        self.status_data = StatusData()
        self.telemetry_data = {}
        self.replay_data = {
            "status": "",
            "speed": 1.0,
            "mission_list": get_mission_list(self.missions_dir)
        }

        self.status_data.serial.available_ports = self.shareable_to_list()

    def generate_websocket_response(self, telemetry_keys="all"):
        return {"version": VERSION, "org": ORG,
                "status": self.generate_status_data(),
                "telemetry_data": self.generate_telemetry_data(telemetry_keys),
                "replay": self.generate_replay_response()}

    def generate_replay_response(self):
        return {"status": self.replay_data["status"],
                "speed": self.replay_data["speed"],
                "mission_list": self.replay_data["mission_list"]}

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

        pass

    def parse_ws_commands(self, ws_cmd):

        try:
            if ws_cmd[0] == "update":
                self.update_websocket()
            if ws_cmd[0] == "replay":
                self.parse_replay_ws_cmd(ws_cmd[1:])
            if ws_cmd[0] == "record":
                self.parse_record_ws_cmd(ws_cmd[1:])

        except IndexError:
            print("Telemetry: Error parsing ws command")

    def replay_set_speed(self, speed: float):

        """Set the playback speed of the replay system."""

        speed = 0.0 if speed < 0 else speed

        if speed == 0.0:
            self.replay_data["status"] = "paused"
        else:
            self.replay_data["status"] = "playing"

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

        if mission_name in self.replay_data["mission_list"]:
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

            self.replay_set_speed(speed=1)
            self.status_data.mission.state = MissionState.RECORDED
            print(f"REPLAY {mission_name} PLAYING")
            return

        raise MissionNotFoundError(mission_name)

    def start_recording(self, mission_name: str, recording_epoch: int) -> None:

        """Starts recording the current mission."""

        if self.status_data.mission.recording:
            raise AlreadyRecordingError

        print("RECORDING START")

        self.mission_path = self.get_filepath_for_proposed_name(mission_name)
        self.mission_path.write_text(f"{1},{recording_epoch}\n")

        self.status_data.mission.name = mission_name
        self.status_data.mission.epoch = recording_epoch
        self.status_data.mission.recording = True

        self.replay_data["mission_list"] = get_mission_list(self.missions_dir)

    def stop_recording(self) -> None:

        """Stops the current recording."""

        print("RECORDING STOP")
        self.status_data.mission = MissionData(state=self.status_data.mission.state)

    def parse_replay_ws_cmd(self, ws_cmd):

        replay_cmd = ws_cmd[0]
        if replay_cmd == "play" and len(ws_cmd) > 1:
            mission_name = ' '.join(ws_cmd[1:])
            try:
                self.play_mission(mission_name)
            except MissionNotFoundError as e:
                print(e.message)

        # Simple stuff
        elif replay_cmd == "play" and len(ws_cmd) == 1:
            print("REPLAY PLAY")
            self.replay_set_speed(speed=1)
        elif replay_cmd == "pause":
            print("REPLAY PAUSE")
            self.replay_set_speed(speed=0)
        elif replay_cmd == "speed":
            print(f"REPLAY SPEED {ws_cmd[1]}")
            self.replay_set_speed(speed=ws_cmd[1])
        elif replay_cmd == "stop":
            self.stop_replay()

        self.update_websocket()

    def parse_record_ws_cmd(self, ws_cmd):

        record_cmd = ws_cmd[0]

        if record_cmd == "start":

            recording_epoch = int(time())
            mission_name = str(recording_epoch) if len(ws_cmd) <= 1 else " ".join(ws_cmd[1:])

            try:
                self.start_recording(mission_name, recording_epoch)
            except AlreadyRecordingError as e:
                print(e.message)

        elif record_cmd == "stop":
            self.stop_recording()

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
                    self.status_data.rocket = RocketData.from_data_block(block_data)
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

    def get_filepath_for_proposed_name(self, mission_name) -> Path:
        self.missions_dir.mkdir(parents=True, exist_ok=True)

        missions_filepath = self.missions_dir.joinpath(f"{mission_name}{MISSION_EXTENSION}")

        if missions_filepath.is_file():
            for i in range(1, 50):
                proposed_filepath = self.missions_dir.joinpath(f"{mission_name}_{i}{MISSION_EXTENSION}")
                if not proposed_filepath.is_file():
                    return proposed_filepath

        return missions_filepath


def _parse_packet_header(header) -> tuple:
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


def _parse_block_header(header) -> tuple:
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
