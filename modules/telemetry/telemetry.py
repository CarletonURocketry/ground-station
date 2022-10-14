import multiprocessing
import math
import os
import random
import struct
import time
import queue
import packets

import data_block
from modules.misc.converter import celsius_to_fahrenheit, metres_to_feet

# Constants
SUBTYPE = {
    0: "debug_message",
    1: "status",
    2: "startup_message",
    3: "altitude_data",
    4: "acceleration_data",
    5: "angular_velocity_data",
    6: "GNSS_location_data",
    7: "GNSS_metadata",
    8: "power_information",
    9: "temperatures",
    "A": "MPU9250_IMU_data",
    "B": "KX134-1211_accelerometer_data"
}

PACKETS = {
    SUBTYPE[3]: packets.AltitudeData,
    SUBTYPE[4]: packets.AccelerationData,
    SUBTYPE[5]: packets.AngularVelocityData,
    SUBTYPE[6]: packets.GNSSLocationData,
    SUBTYPE[7]: packets.GNSSMetaData,
    SUBTYPE["A"]: packets.MPU9250Data,
    SUBTYPE["B"]: packets.KX1341211Data
}

altitude = 0
temp = 22
going_up = True

class Telemetry(multiprocessing.Process):
    def __init__(self, serial_input: multiprocessing.Queue, serial_data_output: multiprocessing.Queue,
                 telemetry_json_output: multiprocessing.Queue):
        super().__init__()

        # Continually add to these
        self.altitude = altitude
        self.temp = temp
        self.going_up = going_up

        self.serial_input = serial_input
        self.serial_data_output = serial_data_output
        self.telemetry_json_output = telemetry_json_output
        self.telemetry_data = {"key": "lol"}

        self.run()

    def run(self):
        while True:
            while not self.serial_data_output.empty():
                self.parse_rx(self.serial_data_output.get())

            # print(f"Telemetry sending sample websocket json")
            self.send_sample_websocket_json()
            time.sleep(.100)

    def send_sample_websocket_json(self):
        random_alternation = int(random.uniform(0, 1000))

        if self.going_up:
            self.temp += random_alternation / 500
        else:
            self.temp -= random_alternation / 500

        if self.temp > 100:
            self.going_up = False
        elif self.temp < 20:
            self.going_up = True

        self.altitude += random.uniform(0, 3)
        metres = self.altitude

        sample_json = {
            "version": "0.1.1",
            "org": "CU InSpace",
            "status": {
                "board": {
                    "connected": "yes"
                },
                "rocket": {
                    "call_sign": "Not a missile",
                    "status_code": 2,
                    "status_text": "POWERED ASCENT",
                    "last_mission_time": 8120
                }
            },
            "telemetry_data": {
                "altitude_data": {
                    "mission_time": "8120",
                    "pressure": {
                        "pascals": "87181"
                    },
                    "altitude": {
                        "m": f"{metres}",
                        "ft": f"{metres_to_feet(metres)}"
                    },
                    "temperature": {
                        "celsius": f"{round(self.temp, 3)}",
                        "fahrenheit": f"{celsius_to_fahrenheit(self.temp)}"
                    }
                },
                "acceleration_data": {
                    "mission_time": "8120",
                    "acceleration": {
                        "ms2": "40",
                        "fts2": "131"
                    }
                },
                "position_data": {
                    "mission_time": "8120",
                    "coordinates": {
                        "lat": "45.385273194259014",
                        "long": "-75.69838116342798"
                    },
                    "gnss_metadata": {
                        "gnss_sat_type": "gps",
                        "gps_sats_in_view": 3,
                        "glonass_sats_in_view": 2,
                        "sats_in_view": 5
                    }
                }
            }
        }

        self.telemetry_json_output.put(sample_json)

    def parse_rx_OLD(self, data):
        # print(f"PARSE_RX: {data}")
        try:
            packet = bytes.fromhex(data)
            # print(packet)
        except ValueError:
            print(f'error: data is {data}')
            return

        call_sign = packet[0:6]

        # remove packet header from rest of data
        packet = packet[12:]

        while len(packet) != 0:

            block_header = struct.unpack('<I', packet[0:4])

            length = (block_header[0] & 0x1f) * 4
            signed = ((block_header[0] >> 5) & 0x1)
            _type = ((block_header[0] >> 6) & 0xf)
            subtype = ((block_header[0] >> 10) & 0x3f)
            dest_addr = ((block_header[0] >> 16) & 0xf)

            if _type == 0 and subtype == 0:
                # this is a signal report
                # RESULT IS BROKEN FOR NOW

                self.serial_input.put('radio get snr')
                # snr = self._read_ser()

                self.serial_input.put('radio get rssi')
                # rssi = self._read_ser()

                print("-----" * 20)
                print(f'{call_sign} has asked for a signal report\n')
                # print(f'the SNR is {snr} and the RSSI is {rssi}')
                print("-----" * 20)

                # logging_info = f'signal report at {time.time()}. SNR is {snr}, RSSI is {rssi}\n'
                # self.log.write(logging_info)

            else:
                payload = packet[4:4 + length]
                try:
                    block = data_block.DataBlock.from_payload(subtype, payload)
                    print("-----" * 20)
                    print(f'{call_sign} sent you a packet:')
                    print(block)
                    print("-----" * 20)
                    logging_info = 'f{block}\n'
                    # self.log.write(logging_info)

                except:
                    print(f'could not parse incoming packet of type {_type}, subtype: {subtype}\n')

            # move to next block
            packet = packet[length + 4:]

        # self.log.flush()
        # os.fsync(self.log.fileno())

    def parse_rx(self, data: str) -> tuple | None:
        # Originally from UI_functions

        # Extract the packet header
        call_sign, length, version, srs_addr, packet_num = _parse_packet_header(data[:24])

        if length <= 24:  # If this packet nothing more than just the header
            return call_sign, length, version, srs_addr, packet_num

        blocks = data[24:]  # Remove the packet header
        # Parse through all blocks
        while blocks != '':
            # Parse block header
            block_header = blocks[:8]
            block_len, crypto_signature, message_type, message_subtype, dest_addr = _parse_block_header(block_header)

            block_len = block_len * 2  # Convert length in bytes to length in hex symbols
            payload = blocks[8: 8 + block_len]

            # Create data if correct packet format was found
            packet = PACKETS.get(SUBTYPE.get(message_subtype))

            print("---"*25)
            print("BLOCK HEADER", block_header)
            print("BLOCK LEN", block_len)
            print("BLOCK DATA", payload)

            packet_data = packet.create_from_raw(payload) if packet else None
            print(f"BLOCK FOR {SUBTYPE.get(message_subtype)} RETURNED {packet_data}")

            # Remove the data we processed from the whole set, and move onto the next data block
            blocks = blocks[8 + block_len:]


# UI_Functions
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
    message_subtype: str
    destination_addr: int
    """
    # header = bin(int(header, 16))  # Convert into binary

    # block_len: int = int(header[0:5], 2) - 4  # Length of block in bytes, excluding header, hence subtract 4
    # crypto_signature: bool = True if int(header[5], 2) == 1 else False  # Check if message has a cryptographic signature

    # Type of message (Ex: The purpose of the block, such as transmitting info to ground station)
    # message_type: int = int(header[6:10], 2)

    # message_subtype: str = SUBTYPE.get(int(header[10:16], 2))  # Type of information that is stored in the block
    # destination_addr: int = int(header[16:20], 2)
    # print("PARSE BLOCK HEADER",block_len, crypto_signature, message_type, message_subtype, destination_addr)

    header = struct.unpack('<I', bytes.fromhex(header))

    block_len = ((header[0] & 0x1f) + 1) * 4
    crypto_signature = ((header[0] >> 5) & 0x1)
    message_type = ((header[0] >> 6) & 0xf)  # 0 - Control, 1 - Command, 2 - Data
    message_subtype = ((header[0] >> 10) & 0x3f)
    destination_addr = ((header[0] >> 16) & 0xf)  # 0 - GStation, 1 - Rocket

    return block_len, crypto_signature, message_type, message_subtype, destination_addr
