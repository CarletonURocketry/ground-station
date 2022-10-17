import multiprocessing
import struct
import time

from modules.telemetry.data_block import DataBlock, DataBlockSubtype


class Telemetry(multiprocessing.Process):
    def __init__(self, serial_input: multiprocessing.Queue, serial_data_output: multiprocessing.Queue,
                 telemetry_json_output: multiprocessing.Queue):
        super().__init__()

        self.serial_input = serial_input
        self.serial_data_output = serial_data_output
        self.telemetry_json_output = telemetry_json_output

        # Telemetry Data holds a dict of the latest copy of received data blocks stored under the subtype name as a key.
        self.telemetry_data = {}
        self.status_data = {
            "board": {
                "connected": "yes"
            },
            "rocket": {
                "call_sign": "Not a missile",
                "status_code": 2,
                "status_name": "POWERED ASCENT",
                "last_mission_time": 8120
            }}

        self.log = "Payloads\n"
        self.run()

    def run(self):
        while True:
            while not self.serial_data_output.empty():
                self.parse_rx(self.serial_data_output.get())

            # print(f"Telemetry sending sample websocket json")
            time.sleep(.100)
            self.telemetry_json_output.put(self.generate_websocket_response())

    def generate_websocket_response(self, telemetry_keys="all"):
        return {"version": "0.2.3", "org": "CU InSpace", "status": self.generate_status_data(),
                "telemetry_data": self.generate_telemetry_data(telemetry_keys)}

    def generate_status_data(self):
        return {"board": self.status_data["board"], "rocket": self.status_data["rocket"]}

    def generate_telemetry_data(self, keys_to_send="all"):
        if keys_to_send == "all":
            keys_to_send = self.telemetry_data.keys()

        telemetry_data_block = {}
        for key in keys_to_send:
            if key in self.telemetry_data.keys():
                telemetry_data_block[key] = self.telemetry_data[key]

        return telemetry_data_block

    def parse_rx(self, data: str) -> tuple | None:
        self.log += data

        # Extract the packet header
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

        if length <= 24:  # If this packet nothing more than just the header
            return call_sign, length, version, srs_addr, packet_num

        blocks = data[24:]  # Remove the packet header

        print("-----" * 20)
        print(f'{str(bytes.fromhex(call_sign))} sent you a packet:')
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

            block_contents = DataBlock.parse(DataBlockSubtype(block_subtype), payload)
            self.telemetry_data[DataBlockSubtype(block_subtype).name.lower()] = dict(block_contents)
            print(block_contents)

            #print("BLOCKHEADER:", _parse_block_header("840C0000"))

            # Remove the data we processed from the whole set, and move onto the next data block
            blocks = blocks[8 + block_len:]
        print("-----" * 20)


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
    header = struct.unpack('<I', bytes.fromhex(header))
    #print("XXXXXXXXXX", header)


    block_len = ((header[0] & 0x1f) + 1) * 4  # Length of the data block
    crypto_signature = ((header[0] >> 5) & 0x1)
    message_type = ((header[0] >> 6) & 0xf)  # 0 - Control, 1 - Command, 2 - Data
    message_subtype = ((header[0] >> 10) & 0x3f)
    destination_addr = ((header[0] >> 16) & 0xf)  # 0 - GStation, 1 - Rocket

    lol = 13634180
    header = struct.pack('<I', lol)
    print("HEADDDDDDDDD", int.from_bytes(header, "little"))

    test = struct.pack('<I?III', 20, False, 2, 3, 0)
    print("LLLLLLLL",test.hex())
    return block_len, crypto_signature, message_type, message_subtype, destination_addr


def make_block(payload) -> tuple:


    #block_len = ((header[0] & 0x1f) + 1) * 4  # Length of the data block
    #crypto_signature = ((header[0] >> 5) & 0x1)
    #message_type = ((header[0] >> 6) & 0xf)  # 0 - Control, 1 - Command, 2 - Data
    #message_subtype = ((header[0] >> 10) & 0x3f)
    #destination_addr = ((header[0] >> 16) & 0xf)  # 0 - GStation, 1 - Rocket

    lol = "13634180"
    header = struct.pack('<I', lol)
    #print("HEADDDDDDDDD",header)
    return header
