from dataclasses import dataclass
from typing import List, Optional
import logging


from modules.telemetry.packet_spec.headers import *
from modules.telemetry.packet_spec.blocks import Block, parse_block_contents, get_block_class
from modules.misc.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransmission:
    """Parsed transmission data from the telemetry process."""

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

    logger.info(packet_header)
    # We can keep unauthorized callsigns but we'll log them as warnings
    from_approved_callsign(packet_header, config.approved_callsigns)
    blocks = packet_bytes[PACKET_HEADER_LENGTH:]  # Remove the packet header

    return ParsedTransmission(packet_header, parse_blocks(packet_header, blocks))


def from_approved_callsign(pkt_hdr: PacketHeader, approved_callsigns: dict[str, str]) -> bool:
    """Checks whether the call sign is recognized"""

    # Ensure packet is from an approved call sign
    if pkt_hdr.callsign in approved_callsigns:
        logger.debug(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
    else:
        logger.warning(f"Incoming packet from unauthorized call sign {pkt_hdr.callsign}")
        return False

    return True


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

        logger.info(block_header)
        block_len = get_block_class(block_header.type).size()
        block_contents = encoded_blocks[BLOCK_HEADER_LENGTH : BLOCK_HEADER_LENGTH + block_len]
        parsed_blocks.append(parse_block_contents(packet_header, block_header, block_contents))
        # Remove the data we processed from the whole set, and move onto the next data block
        encoded_blocks = encoded_blocks[BLOCK_HEADER_LENGTH + block_len :]

    return parsed_blocks
