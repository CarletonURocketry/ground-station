from dataclasses import dataclass, asdict
from typing import List, Optional
import logging


from modules.telemetry.packet_spec.headers import *
from modules.telemetry.packet_spec.blocks import parse_block_contents
from modules.misc.config import Config

logger = logging.getLogger(__name__)


# Dataclasses that allow us to structure the telemetry data
@dataclass
class ParsedBlock:
    """Parsed block data from the telemetry process."""

    block_name: str
    block_header: BlockHeader
    block_contents: dict[str, int | dict[str, int]]


@dataclass
class ParsedTransmission:
    """Parsed transmission data from the telemetry process."""

    packet_header: PacketHeader
    blocks: List[ParsedBlock]


# Parsing functions
def parse_rn2483_transmission(data: str, config: Config) -> Optional[ParsedTransmission]:
    """
    Parses RN2483 Packets and extracts our telemetry payload blocks, returns parsed transmission object if packet
    is valid.
    """
    # List of parsed blocks
    parsed_blocks: list[ParsedBlock] = []

    # Extract the packet header
    data = data.strip()  # Sometimes some extra whitespace
    packet_bytes = bytes.fromhex(data)
    logger.debug(f"Full data string: {data}")
    # TODO Make a generic abstract packet header class to encompass V1 packet header, etc

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

    # Parse through all blocks
    while len(blocks) > 0:
        # Parse block header
        logger.debug(f"Blocks: {blocks}")
        logger.debug(f"Block header: {blocks[:BLOCK_HEADER_LENGTH]}")

        # Catch invalid block headers field values by skipping packet
        try:
            block_header = parse_block_header(blocks[:BLOCK_HEADER_LENGTH])
        except InvalidHeaderFieldValueError as e:
            logger.error(f"{e}, skipping packet")
            return
        logger.info(block_header)

        block_len = len(block_header)
        block_contents = blocks[BLOCK_HEADER_LENGTH : BLOCK_HEADER_LENGTH + block_len]

        # Remove the data we processed from the whole set, and move onto the next data block
        blocks = blocks[BLOCK_HEADER_LENGTH + block_len :]

    return ParsedTransmission(packet_header, parsed_blocks)


def from_approved_callsign(pkt_hdr: PacketHeader, approved_callsigns: dict[str, str]) -> bool:
    """Checks whether the call sign is recognized"""

    # Ensure packet is from an approved call sign
    if pkt_hdr.callsign in approved_callsigns:
        logger.debug(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
    else:
        logger.warning(f"Incoming packet from unauthorized call sign {pkt_hdr.callsign}")
        return False

    return True


def parse_radio_block(
    packet_header: PacketHeader, block_header: BlockHeader, block_contents: bytes
) -> Optional[ParsedBlock]:
    """
    Parses telemetry payload blocks from either parsed packets or stored replays. Block contents are a hex string.
    """

    parsed_contents = parse_block_contents(packet_header, block_header, block_contents)
    # TODO - check name here
    return ParsedBlock(block_header.type.name, block_header, asdict(parsed_contents))
