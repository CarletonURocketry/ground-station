from dataclasses import dataclass
from typing import List, Optional
import logging
import struct

from src.ground_station_v2.radio.packets.headers import (
    PacketHeader,
    BlockType,
    BlockHeader,
    parse_packet_header,
    parse_block_header,
    PACKET_HEADER_LENGTH,
    BLOCK_HEADER_LENGTH,
    CALLSIGN_LENGTH,
    InvalidHeaderFieldValueError,
)
from src.ground_station_v2.radio.packets.blocks import Block, parse_block_contents, get_block_class, InvalidBlockContents
from src.ground_station_v2.config import Config
from time import time

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransmission:
    packet_header: PacketHeader
    blocks: List[Block]


# Parsing functions
def parse_rn2483_transmission(data: str, config: Config) -> Optional[ParsedTransmission]:
    """
    Parses RN2483 Packets and extracts our telemetry payload blocks, returns parsed transmission object if packet
    is valid.
    """

    # Extract the packet header
    data = data.strip()  # Sometimes some extra whitespace
    packet_bytes = bytes.fromhex(data)
    logger.debug(f"Full data string: {data}")

    # Catch unsupported encoding versions by skipping packet
    try:
        packet_header: PacketHeader = parse_packet_header(packet_bytes[:PACKET_HEADER_LENGTH])
    except InvalidHeaderFieldValueError as e:
        logger.error(f"{e}, skipping packet")
        return

    logger.debug(packet_header)
    # We can keep unauthorized callsigns but we'll log them as warnings
    from_approved_callsign(packet_header, config.approved_callsigns)
    blocks = packet_bytes[PACKET_HEADER_LENGTH:]  # Remove the packet header

    return ParsedTransmission(packet_header, parse_blocks(packet_header, blocks))


def from_approved_callsign(pkt_hdr: PacketHeader, approved_callsigns: dict[str, str]) -> bool:
    """Checks whether the call sign is recognized"""

    # Ensure packet is from an approved call sign
    if pkt_hdr.callsign in approved_callsigns:
        logger.debug(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
        return True
    for callsign in approved_callsigns:
        if pkt_hdr.callsign.startswith(callsign):
            logger.debug(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
            return True

    logger.warning(f"Incoming packet from unauthorized call sign {pkt_hdr.callsign}")
    return False

def parse_blocks(packet_header: PacketHeader, encoded_blocks: bytes) -> List[Block]:
    """
    Parses telemetry payload blocks from either parsed packets or stored replays. Block contents are a hex string.
    """

    # List of parsed blocks
    parsed_blocks: list[Block] = []

    # Parse through all encoded_blocks
    while len(encoded_blocks) > 0:
        # Parse block header
        logger.debug(f"encoded_blocks: {encoded_blocks}")
        logger.debug(f"Block header: {encoded_blocks[:BLOCK_HEADER_LENGTH]}")

        # Catch invalid block headers field values by skipping packet
        try:
            block_header = parse_block_header(encoded_blocks[:BLOCK_HEADER_LENGTH])
        except InvalidHeaderFieldValueError as e:
            logger.error(f"{e}, skipping rest of packet")
            return parsed_blocks

        logger.debug(block_header)

        block_len = get_block_class(block_header.type).size()
        block_contents = encoded_blocks[BLOCK_HEADER_LENGTH : BLOCK_HEADER_LENGTH + block_len]

        data_block = None
        try:
            data_block = parse_block_contents(packet_header, block_header, block_contents)
        except InvalidBlockContents as e:
            logger.error(f"{e}")

        if data_block is not None:
            logger.debug(data_block)
            parsed_blocks.append(data_block)
        # Remove the data we processed from the whole set, and move onto the next data block
        encoded_blocks = encoded_blocks[BLOCK_HEADER_LENGTH + block_len :]

    return parsed_blocks

def create_fake_packet() -> str:
    """
    Creates a fake packet with sample telemetry data for testing purposes.
    Returns a hex string representation of the raw packet bytes that can be
    parsed by parse_rn2483_transmission().
    """
    timestamp = int(time() * 1000) & 0xFFFF  # Mask to 16 bits
    packet_num = 1
    block_count = 3

    # Create packet header bytes (callsign padded to 9 chars + timestamp + block count + packet num)
    callsign = "VA3ZAJ".ljust(CALLSIGN_LENGTH, '\x00')
    packet_header_bytes = callsign.encode('ascii') + struct.pack("<HBB", timestamp, block_count, packet_num)

    # Create block bytes
    block_bytes = b""

    # Temperature block: block header (type=0x02, count=1) + contents (time, temp)
    block_bytes += struct.pack("<BB", BlockType.TEMPERATURE, 1)  # Block header
    block_bytes += struct.pack("<hi", 1000, 25000)  # 1 second, 25°C (milli-degrees)

    # Pressure block: block header (type=0x03, count=1) + contents (time, pressure)
    block_bytes += struct.pack("<BB", BlockType.PRESSURE, 1)  # Block header
    block_bytes += struct.pack("<hI", 1500, 101325)  # 1.5 seconds, ~1 atm

    # Linear acceleration block: block header (type=0x04, count=1) + contents (time, x, y, z)
    block_bytes += struct.pack("<BB", BlockType.LINEAR_ACCELERATION, 1)  # Block header
    block_bytes += struct.pack("<hhhh", 2000, 0, 0, 981)  # 2 seconds, ~9.81 m/s² in z

    # Combine and return as hex string
    full_packet = packet_header_bytes + block_bytes
    return full_packet.hex()
    
    
    
