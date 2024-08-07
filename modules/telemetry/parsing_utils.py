from dataclasses import dataclass
from typing import List, Optional
import logging


from modules.telemetry.v1.block import (
    PacketHeader,
    BlockHeader,
    DeviceAddress,
    UnsupportedEncodingVersionError,
    InvalidHeaderFieldValueError,
)
import modules.telemetry.v1.data_block as v1db
from modules.misc.config import Config

MIN_SUPPORTED_VERSION: int = 1
MAX_SUPPORTED_VERSION: int = 1

logger = logging.getLogger(__name__)


# Dataclasses that allow us to structure the telemetry data
@dataclass
class ParsedBlock:
    """Parsed block data from the telemetry process."""

    # mission_time: int
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
    logger.debug(f"Full data string: {data}")
    # TODO Make a generic abstract packet header class to encompass V1 packet header, etc

    # Catch unsupported encoding versions by skipping packet
    try:
        pkt_hdr = PacketHeader.from_hex(data[:32])
    except UnsupportedEncodingVersionError as e:
        logger.error(f"{e}, skipping packet")
        return

    # We can keep unauthorized callsigns but we'll log them as warnings
    from_approved_callsign(pkt_hdr, config.approved_callsigns)

    if len(pkt_hdr) <= 32:  # If this packet nothing more than just the header
        logger.debug(f"{pkt_hdr}")

    blocks = data[32:]  # Remove the packet header

    # Parse through all blocks
    while blocks != "":
        # Parse block header
        logger.debug(f"Blocks: {blocks}")
        logger.debug(f"Block header: {blocks[:8]}")

        # Catch invalid block headers field values by skipping packet
        try:
            block_header = BlockHeader.from_hex(blocks[:8])
        except InvalidHeaderFieldValueError as e:
            logger.error(f"{e}, skipping packet")
            return

        # Select block contents
        block_len = len(block_header) * 2  # Convert length in bytes to length in hex symbols
        block_contents = blocks[8:block_len]
        logger.debug(f"Block info: {block_header}")

        # Check if message is destined for ground station for processing
        if block_header.destination in [DeviceAddress.GROUND_STATION, DeviceAddress.MULTICAST]:
            cur_block = parse_radio_block(pkt_hdr.version, block_header, block_contents)
            if cur_block:
                parsed_blocks.append(cur_block)  # Append parsed block to list
        else:
            logger.warning("Invalid destination address")

        # Remove the data we processed from the whole set, and move onto the next data block
        blocks = blocks[block_len:]
    return ParsedTransmission(pkt_hdr, parsed_blocks)


def from_approved_callsign(pkt_hdr: PacketHeader, approved_callsigns: dict[str, str]) -> bool:
    """Checks whether the call sign is recognized"""

    # Ensure packet is from an approved call sign
    if pkt_hdr.callsign in approved_callsigns:
        logger.debug(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
    else:
        logger.warning(f"Incoming packet from unauthorized call sign {pkt_hdr.callsign}")
        return False

    return True


def parse_radio_block(pkt_version: int, block_header: BlockHeader, hex_block_contents: str) -> Optional[ParsedBlock]:
    """
    Parses telemetry payload blocks from either parsed packets or stored replays. Block contents are a hex string.
    """

    # Working with hex strings until this point.
    # Hex/Bytes Demarcation point
    logger.debug(
        f"Parsing v{pkt_version} type {block_header.message_type} subtype {block_header.message_subtype} contents: \
            {hex_block_contents}"
    )
    block_bytes: bytes = bytes.fromhex(hex_block_contents)

    # Convert message subtype string to enum
    try:
        block_subtype = v1db.DataBlockSubtype(block_header.message_subtype)
    except ValueError:
        logger.error(f"Invalid data block subtype {block_header.message_subtype}!")
        return

    # Use the appropriate parser for the block subtype enum
    try:
        # TODO Make an interface to support multiple v1/v2/v3 objects
        block_contents = v1db.DataBlock.parse(block_subtype, block_bytes)
    except NotImplementedError:
        logger.warning(
            f"Block parsing for type {block_header.message_type}, with subtype {block_header.message_subtype} not \
            implemented!"
        )
        return
    except v1db.DataBlockException as e:
        logger.error(e)
        logger.error(f"Block header: {block_header}")
        logger.error(f"Block contents: {hex_block_contents}")
        return

    block_name = block_subtype.name.lower()

    logger.debug(str(block_contents))

    # TODO fix at some point
    # if block == DataBlockSubtype.STATUS:
    #     self.status.rocket = jsp.RocketData.from_data_block(block)
    #     return

    return ParsedBlock(block_name, block_header, dict(block_contents))  # type: ignore
