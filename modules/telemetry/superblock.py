#! /usr/bin/env python3
import os
import struct
import datetime
import sys


class Flight:
    def __init__(self, entry):
        parts = struct.unpack("<III", entry)
        self.first_block = parts[0]
        self.num_blocks = parts[1]
        self.time = datetime.datetime.fromtimestamp(parts[2], datetime.timezone.utc)
        self.timestamp = parts[2]

    def to_bytes(self):
        return struct.pack("<III", self.first_block, self.num_blocks, self.timestamp)

    def is_valid(self):
        # Check for reasonable values
        return False if self.first_block == 0 or self.num_blocks == 0 or self.time == 0 else True


class SuperBlock:
    MAGIC = b'CUInSpac'

    def __init__(self, block):
        if len(block) != 512:
            raise ValueError("Invalid Superblock")

        if block[0x0:0x8] != SuperBlock.MAGIC or block[0x1f8:0x200] != SuperBlock.MAGIC:
            raise ValueError("Invalid Superblock")

        self.version = block[0x09]
        self.continued = not not (block[0x09] & 1)

        self.partition_length = struct.unpack("<I", block[0x0c:0x10])[0]

        self.flights = list()
        self.flight_blocks = 1
        for i in range(32):
            flight_start = 0x60 + (12 * i)
            flight_entry = block[flight_start:flight_start + 12]
            flight_obj = Flight(flight_entry)
            if not flight_obj.is_valid():
                break
            self.flights.append(flight_obj)
            self.flight_blocks += flight_obj.num_blocks

    def output(self, output_dd_cmd: bool = False):
        print(f"Logging Version: {self.version}")
        print(f"First flight continued from previous partition: {'yes' if self.continued else 'no'}")
        print(f"Partition length: {self.partition_length}")
        print()

        flight_blocks = 0
        for i, flight in enumerate(self.flights):
            print(f"Flight {i} -> start: {flight.first_block}, length: {flight.num_blocks}, time: {flight.timestamp}")
            flight_blocks = flight.first_block + flight.num_blocks
        print()

        if output_dd_cmd:
            print(f"Last block: {flight_blocks}")
            print(f"To copy full SD card image, use:    dd if=[disk] of=full bs=512 count={flight_blocks + 2049}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # No arguments
        exit(0)

    # File size
    infile = sys.argv[1]
    file_size = os.stat(infile).st_size

    with open(infile, "rb") as f:
        # Skip MBR and the rest of first sector to get to superblock
        # (512 bytes is just superblock, anything larger should be the full sd card image)
        # If it's a .cuinspace telemetry file, first block is a superblock so don't skip.
        if ".cuinspace" not in infile and file_size > 512:
            f.seek(512 * 2048)
        sb = SuperBlock(f.read(512))

        sb.output(True)
