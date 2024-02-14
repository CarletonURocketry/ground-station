# Replays sensor packets from the mission file
# Outputs data blocks to the UI
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini)
import logging
import struct
from pathlib import Path
from queue import Queue
from time import time, sleep
from typing import BinaryIO

from modules.telemetry.block import RadioBlockType, SDBlockSubtype
from modules.telemetry.superblock import find_superblock

# Set up logging
logger = logging.getLogger(__name__)


def parse_sd_block_header(header_bytes: bytes) -> tuple[int, int, int]:
    """
    Parses a sd block header string into its information components and returns them in a tuple.

    block_class: int
    block_subtype: int
    block_length: int
    """

    header = struct.unpack("<HH", header_bytes)

    block_class = header[0] & 0x3F  # SD Block Class
    block_subtype = header[0] >> 6  # Block subtype (Altitude, IMU, GNSS, etc)
    block_length = header[1]  # Length of entire block in bytes

    return block_class, block_subtype, block_length


class TelemetryReplay:
    def __init__(
            self,
            replay_payloads: Queue[tuple[int, int, str]],
            replay_input: Queue[str],
            replay_speed: int,
            replay_path: Path,
            replay_version: int
    ):
        super().__init__()

        # Replay buffers (Input and output)
        self.replay_payloads: Queue[tuple[int, int, str]] = replay_payloads
        self.replay_input: Queue[str] = replay_input

        # Misc replay
        self.replay_path = replay_path

        # Loop data
        self.last_loop_time = int(time() * 1000)
        self.total_time_offset = 0
        self.speed = replay_speed
        self.block_count = 0

        if replay_version == 0:
            # Replay superblock
            superblock_result = find_superblock(self.replay_path)
            if superblock_result is None:
                raise ValueError(f"Could not find superblock in {self.replay_path}")
            sb_addr, mission_sb = superblock_result

            with open(self.replay_path, "rb") as file:
                for flight in mission_sb.flights:
                    _ = file.seek((sb_addr + flight.first_block) * 512)
                    self.run(file, flight.num_blocks)
        else:
            # Replay raw radio transmission file
            with open(self.replay_path, "r") as file:
                for line in file:
                    replay_data = (RadioBlockType.DATA, 0, line)
                    self.replay_payloads.put(replay_data)
                    #sleep(1)

    def run(self, file: BinaryIO, num_blocks: int):
        """Run loop"""
        while True:
            if self.speed > 0:
                self.read_next_sd_block(file, num_blocks)

            if not self.replay_input.empty():
                self.parse_input_command(self.replay_input.get())

    def parse_input_command(self, data: str) -> None:
        cmd_list = data.split(" ")
        match cmd_list[0]:
            case "speed":
                self.speed = float(cmd_list[1])
                # Reset loop time so resuming playback doesn't skip the time it was paused
                self.last_loop_time = int(time() * 1000)
            case _:
                raise NotImplementedError(f"Replay command of {cmd_list} invalid.")

    def read_next_sd_block(self, file: BinaryIO, num_blocks: int):
        """Reads the next stored block and outputs it"""
        if self.block_count <= ((num_blocks * 512) - 4):
            try:
                block_header = file.read(4)
                block_class, block_subtype, block_length = parse_sd_block_header(block_header)
                block_data = file.read(block_length - 4)
                self.block_count += block_length
            except IOError as error:
                logger.error(f"{error}")
                return

            # TODO Change block_type to use a matrix that compares SDBlockTypes and Radio blocks
            if block_class != SDBlockSubtype.TELEMETRY_DATA:
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
            logger.info("Flight replay finished")
            self.speed = 0

    def output_replay_data(self, block_type: int, block_subtype: int, block_data: bytes):
        # block_data should NOT contain block header and should be hex
        replay_data = (block_type, block_subtype, block_data.hex())
        self.replay_payloads.put(replay_data)
