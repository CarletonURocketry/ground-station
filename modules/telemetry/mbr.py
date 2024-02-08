import struct


class CHSAddr:
    def __init__(self, addr: bytes) -> None:
        self.cylinder: int = addr[2] | ((addr[1] & 0xC0) << 2)
        self.head: int = addr[0]
        self.sector: int = addr[1] & 0x3F


class MBRPartition:
    def __init__(self, entry: bytes) -> None:
        self.valid: bool = ((entry[0] & ~(1 << 7)) == 0) and (entry[4] != 0)
        self.bootable: bool = bool(entry[0] & (1 << 7))
        self.first_sector_chs: CHSAddr = CHSAddr(entry[1:4])
        self.type: int = entry[4]
        self.last_sector_chs: CHSAddr = CHSAddr(entry[5:8])
        self.first_sector_lba: int = struct.unpack("<I", entry[8:12])[0]
        self.num_sectors: int = struct.unpack("<I", entry[12:16])[0]


class MBR:
    def __init__(self, data: bytes) -> None:
        if len(data) != 512 or data[510] != 0x55 or data[511] != 0xAA:
            raise ValueError("Invalid MBR.")

        self.partitions: list[MBRPartition] = list()
        for i in range(4):
            part_start = 446 + (16 * i)
            part_entry = data[part_start: part_start + 16]
            partition = MBRPartition(part_entry)
            if partition.valid:
                self.partitions.append(partition)
                # print(f"PARTITION: {partition.type} {partition.valid} "
                #       f"{partition.first_sector_lba} {partition.num_sectors}")
