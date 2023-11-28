import struct
import sys


class CHSAddr:
    def __init__(self, addr):
        self.cylinder = addr[2] | ((addr[1] & 0xc0) << 2)
        self.head = addr[0]
        self.sector = addr[1] & 0x3f


class MBRPartition:
    def __init__(self, entry):
        self.valid = ((entry[0] & ~(1 << 7)) == 0) and (entry[4] != 0)
        self.bootable = entry[0] & (1 << 7)
        self.first_sector_chs = CHSAddr(entry[1:4])
        self.type = entry[4]
        self.last_sector_chs = CHSAddr(entry[5:8])
        self.first_sector_lba = struct.unpack("<I", entry[8:12])[0]
        self.num_sectors = struct.unpack("<I", entry[12:16])[0]


class MBR:
    def __init__(self, data):
        if len(data) != 512 or data[510] != 0x55 or data[511] != 0xAA:
            raise ValueError("Invalid MBR.")

        self.partitions = list()
        for i in range(4):
            part_start = 446 + (16 * i)
            part_entry = data[part_start:part_start + 16]
            partition = MBRPartition(part_entry)
            if partition.valid:
                self.partitions.append(partition)
                #print(f"PARTITION: {partition.type} {partition.valid} {partition.first_sector_lba} {partition.num_sectors}")
