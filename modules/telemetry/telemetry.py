# Telemetry to parse radio packets, keep history and to log everything
# Incoming information comes from rn2483_radio_payloads in payload format
# Outputs information to telemetry_json_output in friendly json for UI
#
# Authors:
# Thomas Selwyn (Devil)
import time

from struct import unpack
from time import sleep, time
from pathlib import Path
from modules.telemetry.data_block import DataBlock, DataBlockSubtype
from modules.telemetry.replay import TelemetryReplay
from multiprocessing import Queue, Process, Value
from multiprocessing.shared_memory import ShareableList


def shareable_to_list(shareable_list, empty_padding=True) -> list:
    new_list = [""]
    try:
        new_list = [""] * len(shareable_list)

        for i in range(len(shareable_list)):
            new_list[i] = str(shareable_list[i])

        if empty_padding:
            new_list = ' '.join(new_list).split()

    except TypeError:
        print(f"{new_list}")

    return new_list


class Telemetry(Process):
    def __init__(self, serial_connected: Value, serial_connected_port: Value, serial_ports: ShareableList,
                 radio_payloads: Queue,
                 telemetry_json_output: Queue, telemetry_ws_commands: Queue):
        super().__init__()

        self.radio_payloads = radio_payloads
        self.telemetry_json_output = telemetry_json_output

        self.telemetry_ws_commands = telemetry_ws_commands

        self.serial_ports = serial_ports
        self.serial_connected = serial_connected
        self.serial_connected_port = serial_connected_port

        # Telemetry Data holds a dict of the latest copy of received data blocks stored under the subtype name as a key.
        self.telemetry_data = {}
        self.status_data = {}
        self.replay_data = {}

        # Mission Path
        self.missions_dir = Path.cwd().joinpath("missions")
        self.missions_dir.mkdir(parents=True, exist_ok=True)
        self.mission_path = None

        # Replay System
        self.replay = None
        self.replay_input = Queue()
        self.replay_output = Queue()

        self.reset_data()

        self.run()

    def run(self):
        while True:

            while not self.telemetry_ws_commands.empty():
                self.parse_ws_commands(self.telemetry_ws_commands.get())

            match self.status_data["mission"]["type"]:
                case 0:
                    # LIVE DATA FROM RADIO
                    while not self.radio_payloads.empty():
                        self.parse_rn2483_payload(self.radio_payloads.get())

                case 1:
                    # RECORDED DATA FROM REPLAY SYSTEM
                    while not self.replay_output.empty():
                        block_type, block_subtype, block_data = self.replay_output.get()
                        self.parse_replay_payload(block_type, block_subtype, block_data)

            # TEMP Serial port change detected :)
            if len(shareable_to_list(self.serial_ports, True)) != len(self.status_data["serial"]["available_ports"]):
                self.update_websocket()

            if bool(self.serial_connected.value) != bool(self.status_data["rn2483_radio"]["connected"]):
                self.update_websocket()
            sleep(.1)

    def update_websocket(self):
        self.telemetry_json_output.put(self.generate_websocket_response())

    def generate_websocket_response(self, telemetry_keys="all"):
        return {"version": "0.4.0", "org": "CU InSpace", "status": self.generate_status_data(),
                "telemetry_data": self.generate_telemetry_data(telemetry_keys),
                "replay": self.generate_replay_response()}

    def generate_replay_response(self):
        return {"status": self.replay_data["status"],
                "speed": self.replay_data["speed"],
                "mission_list": self.replay_data["mission_list"]}

    def generate_replay_mission_list(self):
        return [name.stem for name in self.missions_dir.glob("*.mission") if name.is_file()]

    def generate_status_data(self):
        self.status_data["rn2483_radio"]["connected"] = bool(self.serial_connected.value)
        self.status_data["rn2483_radio"]["connected_port"] = self.serial_connected_port[0]
        self.status_data["serial"]["available_ports"] = shareable_to_list(self.serial_ports)

        return self.status_data

    def generate_telemetry_data(self, keys_to_send="all"):
        if keys_to_send == "all":
            keys_to_send = self.telemetry_data.keys()

        telemetry_data_block = {}
        for key in keys_to_send:
            if key in self.telemetry_data.keys():
                telemetry_data_block[key] = self.telemetry_data[key]

        return telemetry_data_block

    def parse_ws_commands(self, ws_cmd):
        try:
            if ws_cmd[1] == "update":
                self.telemetry_json_output.put(self.generate_websocket_response())
            if ws_cmd[1] == "replay":
                self.parse_replay_ws_cmd(ws_cmd)
            if ws_cmd[1] == "record":
                self.parse_record_ws_cmd(ws_cmd)

        except IndexError:
            print("Telemetry: Error parsing ws command")

    def parse_replay_ws_cmd(self, ws_cmd):
        try:
            match ws_cmd[2]:
                case "play":

                    mission_name = ' '.join(ws_cmd[3:])
                    if mission_name in self.replay_data["mission_list"]:
                        self.status_data["mission"]["name"] = mission_name

                        replay_mission_filepath = self.missions_dir.joinpath(f"{mission_name}.mission")
                        if self.replay is None:
                            self.replay = Process(target=TelemetryReplay,
                                                  args=(self.replay_output, self.replay_input, replay_mission_filepath))
                            self.replay.start()
                        self.replay_data["status"] = "playing"
                        self.status_data["mission"]["type"] = 1
                        print(f"REPLAY {mission_name} PLAYING")
                    else:
                        print(f"REPLAY {mission_name} DOES NOT EXIST")

                case "pause":
                    print("REPLAY PAUSE")

                    self.replay_data["speed"] = 0
                    self.replay_data["status"] = "paused"
                case "speed":
                    print(f"REPLAY SPEED {ws_cmd[3]}")

                    self.replay_data["speed"] = 0 if float(ws_cmd[3]) < 0 else float(ws_cmd[3])
                    if self.replay_data["speed"] == 0:
                        self.replay_data["status"] = "paused"
                case "stop":
                    print("REPLAY STOP")
                    self.replay.terminate()
                    self.replay = None

                    self.reset_data()

            self.update_websocket()

        except IndexError:
            print("Telemetry: Error parsing ws command")

    def reset_data(self):
        self.telemetry_data = {}
        self.status_data = {
            "mission": {
                "name": "",
                "epoch": -1,
                "type": -1,
                "recording": False
            },
            "serial": {
                "available_ports": [""]
            },
            "rn2483_radio": {
                "connected": False,
                "connected_port": ""
            },
            "rocket": {
                "call_sign": "Not a missile",
                "status": {
                    "status_code": 0,
                    "status_name": "IDLE"
                },
                "last_mission_time": -1
            }
        }
        self.replay_data = {
            "status": "",
            "speed": 1.0,
            "mission_list": self.generate_replay_mission_list()
        }

        self.status_data["serial"]["available_ports"] = shareable_to_list(self.serial_ports, True)

    def parse_record_ws_cmd(self, ws_cmd):
        try:
            if ws_cmd[2] == "start" and not self.status_data["recording"]:
                print("RECORDING START")

                recording_epoch = int(time())
                mission_name = str(recording_epoch) if len(ws_cmd) <= 2 else " ".join(ws_cmd[3:])

                self.mission_path = self.get_filepath_for_proposed_name(mission_name)
                self.mission_path.write_text(f"{1},{recording_epoch}\n")

                self.status_data["mission"]["name"] = mission_name
                self.status_data["mission"]["epoch"] = recording_epoch
                self.status_data["mission"]["recording"] = True

                self.replay_data["mission_list"] = self.generate_replay_mission_list()
            elif ws_cmd[2] == "start":
                print("RECORDING HAS ALREADY STARTED. TRY STOPPING FIRST")

            if ws_cmd[2] == "stop":
                print("RECORDING STOP")

                self.status_data["mission"]["name"] = ""
                self.status_data["mission"]["epoch"] = -1
                self.status_data["mission"]["recording"] = False

        except IndexError:
            print("Telemetry: Error parsing ws command")

    def parse_replay_payload(self, block_type: int, block_subtype: int, block_contents: DataBlock):

        if block_contents.mission_time > self.status_data["rocket"]["last_mission_time"]:
            self.status_data["rocket"]["last_mission_time"] = block_contents.mission_time

        self.telemetry_data[DataBlockSubtype(block_subtype).name.lower()] = dict(block_contents)

        # print(block_contents)

        self.update_websocket()

    def parse_rn2483_payload(self, data: str):

        # Extract the packet header
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

        if length <= 24:  # If this packet nothing more than just the header
            print(call_sign, length, version, srs_addr, packet_num)

        blocks = data[24:]  # Remove the packet header

        print("-----" * 20)
        print(f'Rocket - {bytes.fromhex(call_sign).decode("utf-8")} - sent you a packet:')

        # Parse through all blocks
        # TODO Catch type&subtype 0 and do a signal report.
        #  self.serial_input.put('radio get snr')
        #  # snr = self._read_ser()
        #  self.serial_input.put('radio get rssi')
        #  # rssi = self._read_ser()

        while blocks != '':
            # Parse block header
            block_header = blocks[:8]
            block_len, crypto_signature, block_type, block_subtype, dest_addr = _parse_block_header(block_header)

            block_len = block_len * 2  # Convert length in bytes to length in hex symbols
            payload = bytes.fromhex(blocks[8: 8 + block_len])

            if self.status_data["recording"]:
                # offset = int(time.time() * 1000) - self.status_data["recording_epoch"]
                with open(f'{self.mission_path}', 'a') as mission:
                    mission.write(f"{block_type},{block_subtype},{payload.hex()}\n")

            block_contents = DataBlock.parse(DataBlockSubtype(block_subtype), payload)
            if block_contents.mission_time > self.status_data["rocket"]["last_mission_time"]:
                self.status_data["rocket"]["last_mission_time"] = block_contents.mission_time

            self.telemetry_data[DataBlockSubtype(block_subtype).name.lower()] = dict(block_contents)

            print(block_contents)

            # Remove the data we processed from the whole set, and move onto the next data block
            blocks = blocks[8 + block_len:]
        print("-----" * 20)

        self.telemetry_json_output.put(self.generate_websocket_response())

    def get_filepath_for_proposed_name(self, mission_name) -> Path:
        self.missions_dir.mkdir(parents=True, exist_ok=True)

        missions_filepath = self.missions_dir.joinpath(f"{mission_name}.mission")

        if missions_filepath.is_file():
            for i in range(1, 50):
                proposed_filepath = self.missions_dir.joinpath(f"{mission_name}_{i}.mission")
                if not proposed_filepath.is_file():
                    return proposed_filepath

        return missions_filepath


def _parse_packet_header(header) -> tuple:
    """
    Returns the packet header string's informational components in a tuple.

    length: int
    version: int
    src_addr: int
    packet_num: int
    """

    # Extract call sign in hex
    call_sign: str = header[0:12]

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
    crypto_signature = ((header[0] >> 5) & 0x1)
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
