# Replays sensor packets from the mission file
# Outputs data blocks to the UI
#
# Authors:
# Thomas Selwyn (Devil)
import logging
import struct
from time import time, sleep
from multiprocessing import Queue

from pathlib import Path
from typing import BinaryIO

from modules.telemetry.block import RadioBlockType, SDBlockClassType
from modules.telemetry.superblock import SuperBlock


def parse_sd_block_header(header_bytes: bytes):
    """
    Parses a sd block header string into its information components and returns them in a tuple.

    block_class: int
    block_subtype: int
    block_length: int
    """

    header = struct.unpack('<HH', header_bytes)

    block_class = header[0] & 0x3f  # SD Block Class
    block_subtype = header[0] >> 6  # Block subtype (Altitude, IMU, GNSS, etc)
    block_length = header[1]        # Length of entire block in bytes

    return block_class, block_subtype, block_length


class TelemetryReplay:
    def __init__(self, replay_payloads: Queue, replay_input: Queue, replay_speed: int, replay_path: Path):

        # Replay buffers (Input and output)
        self.replay_payloads = replay_payloads
        self.replay_input = replay_input

        # Misc replay
        self.replay_path = replay_path

        # Loop data
        self.last_loop_time = int(time() * 1000)
        self.total_time_offset = 0
        self.speed = replay_speed
        self.block_count = 0

        with open(self.replay_path, "rb") as file:
            mission_sb = SuperBlock.from_bytes(file.read(512))

            for flight in mission_sb.flights:
                file.seek(flight.first_block * 512)
                self.run(file, flight.num_blocks)

    def run(self, file: BinaryIO, num_blocks: int):
        """ Run loop """
        while True:
            if self.speed > 0:
                self.read_next_sd_block(file, num_blocks)

            if not self.replay_input.empty():
                self.parse_input_command(self.replay_input.get())

    def parse_input_command(self, data: str):
        split = data.split(" ")
        match split[0]:
            case "speed":
                self.speed = float(split[1])
                # Reset loop time so resuming playback doesn't skip the time it was paused
                self.last_loop_time = int(time() * 1000)

    def read_next_sd_block(self, file: BinaryIO, num_blocks: int):
        """ Reads the next stored block and outputs it """
        if self.block_count <= ((num_blocks * 512) - 4):
            try:
                block_header = file.read(4)
                block_class, block_subtype, block_length = parse_sd_block_header(block_header)
                block_data = file.read(block_length - 4)
                self.block_count += block_length

            except IOError as e:
                print(e.message())
                return

            # TODO Change block_type to use a matrix that compares SDBlockTypes and Radio blocks
            if block_class != SDBlockClassType.TELEMETRY_DATA:
                return

            # The telemetry file assumes everything is in radio format
            block_class = RadioBlockType.DATA  # Telemetry Data

            # First four bytes in block data is always mission time.
            block_time = struct.unpack("<I", block_data[:4])[0]

            # Calculate where we should be
            current_loop_time = int(time() * 1000)
            self.total_time_offset += float(current_loop_time - self.last_loop_time) * self.speed

            # Sleep until it's the blocks time to shine
            if self.total_time_offset < block_time:
                next_block_wait = (block_time - self.total_time_offset) / self.speed
                sleep(next_block_wait / 1000)

            # Output the block
            self.last_loop_time = current_loop_time
            self.output_replay_data(block_class, block_subtype, block_data)
        else:
            logging.info("Flight replay finished")
            self.speed = 0

    def output_replay_data(self, block_type: int, block_subtype: int, block_data: bytes):
        # block_data should NOT contain block header and should be hex
        replay_data = (block_type, block_subtype, block_data.hex())
        self.replay_payloads.put(replay_data)
