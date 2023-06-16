#! /usr/bin/env python3
import os
import struct
import sys
import datetime as dt
from typing import Self


class Flight:
    def __init__(self, first_block: int, num_blocks: int, timestamp: int):
        super().__init__()
        self.first_block: int = first_block
        self.num_blocks: int = num_blocks
        self.timestamp: int = timestamp

    @classmethod
    def from_bytes(cls, block: bytes) -> Self:
        parts = struct.unpack("<III", block)
        first_block = parts[0]
        num_blocks = parts[1]
        timestamp = parts[2]
        return Flight(first_block, num_blocks, timestamp)

    def to_bytes(self):
        return struct.pack("<III", self.first_block, self.num_blocks, self.timestamp)

    @property
    def time(self) -> dt.datetime:
        return dt.datetime.fromtimestamp(self.timestamp, dt.timezone.utc)

    def is_valid(self):
        # Check for reasonable values
        return False if self.first_block == 0 or self.num_blocks == 0 or self.timestamp == 0 else True


class SuperBlock:
    MAGIC = b"CUInSpac"

    def __init__(
        self, version: int = 1, continued: bool = False, partition_length: int = 0, flights: list[Flight] | None = None
    ):
        super().__init__()
        self.version: int = version
        self.continued: bool = continued
        self.partition_length: int = partition_length
        self.flights: list[Flight] = flights if flights is not None else []

        self.flight_blocks: int = 1
        for flight in self.flights:
            self.flight_blocks += flight.num_blocks

    @classmethod
    def from_bytes(cls, block: bytes) -> Self:
        """Generates the Superblock data object from bytes"""
        if len(block) != 512:
            raise ValueError("Invalid Superblock")

        if block[0x0:0x8] != SuperBlock.MAGIC or block[0x1F8:0x200] != SuperBlock.MAGIC:
            raise ValueError("Invalid Superblock")

        version = int.from_bytes(block[0x08:0x09], "little")
        continued = not not int.from_bytes(block[0x09:0x0A], "little") & (1 << 7)

        partition_length = struct.unpack("<I", block[0x0C:0x10])[0]

        flights: list[Flight] = list()
        flight_blocks = 1
        for i in range(32):
            flight_start = 0x60 + (12 * i)
            flight_entry = block[flight_start : flight_start + 12]
            flight_obj = Flight.from_bytes(flight_entry)
            if not flight_obj.is_valid():
                continue
            flights.append(flight_obj)
            flight_blocks += flight_obj.num_blocks
        return SuperBlock(version, continued, partition_length, flights)

    def to_bytes(self) -> bytes:
        """Returns the Superblock data object in bytes"""
        block: bytearray = bytearray(b"\x00" * 512)
        block[0x0:0x8] = SuperBlock.MAGIC

        block[0x08:0x09] = int(self.version).to_bytes(1, "little")
        block[0x09:0x0A] = int(self.continued << 7).to_bytes(1, "little")
        block[0xC:0x10] = struct.pack("<I", self.partition_length)

        for i in range(len(self.flights)):
            flight_start = 0x60 + (12 * i)
            block[flight_start : flight_start + 12] = self.flights[i].to_bytes()

        block[0x1F8:0x200] = SuperBlock.MAGIC
        return bytes(block)

    def output(self, output_misc: bool = False, output_dd_cmd: bool = False):
        if output_misc:
            print(f"Superblock Version: {self.version}")
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # No arguments
        exit(0)

    # File size
    infile = sys.argv[1]
    file_size = os.stat(infile).st_size

    with open(infile, "rb") as f:
        # Skip MBR and the rest of first sector to get to superblock
        # (512 bytes is just superblock, anything larger should be the full sd card image)
        # If it's a cuinspace telemetry file, first block is a superblock so don't skip.
        if ".mission" not in infile and file_size > 512:
            _ = f.seek(512 * 2048)
        sb = SuperBlock.from_bytes(f.read(512))

        sb.output(True)
