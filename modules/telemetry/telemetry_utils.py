from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging


from modules.telemetry.v1.block import PacketHeader, BlockHeader, DeviceAddress
import modules.telemetry.v1.data_block as v1db
from modules.misc.config import Config

MISSION_EXTENSION: str = "mission"
FILE_CREATION_ATTEMPT_LIMIT: int = 50
SUPPORTED_ENCODING_VERSION: int = 1

logger = logging.getLogger(__name__)


# Helper functions
def mission_path(mission_name: str, missions_dir: Path, file_suffix: int = 0) -> Path:
    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}{'' if file_suffix == 0 else f'_{file_suffix}'}.{MISSION_EXTENSION}")


def get_filepath_for_proposed_name(mission_name: str, missions_dir: Path) -> Path:
    """Obtains filepath for proposed name, with a maximum of giving a suffix 50 times before failing."""
    file_suffix = 1
    missions_filepath = mission_path(mission_name, missions_dir)

    while missions_filepath.is_file() and file_suffix < FILE_CREATION_ATTEMPT_LIMIT:
        missions_filepath = mission_path(mission_name, missions_dir, file_suffix)
        file_suffix += 1

    if file_suffix >= FILE_CREATION_ATTEMPT_LIMIT:
        raise ValueError(f"Too many mission files already exist with name {mission_name}.")

    return missions_filepath


@dataclass
class ParsedBlock:
    """Parsed block data from the telemetry process."""

    # mission_time: int
    block_name: str
    block_header: BlockHeader
    block_contents: v1db.DataBlock


@dataclass
class ParsedTransmission:
    """Parsed transmission data from the telemetry process."""

    packet_header: PacketHeader
    blocks: List[ParsedBlock]


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

    try:
        block_subtype = v1db.DataBlockSubtype(block_header.message_subtype)
        block_contents = v1db.DataBlock.parse(block_subtype, block_bytes)
        block_name = block_subtype.name.lower()

        logger.debug(f"Data block parsed with mission time {block_contents.mission_time}")
        logger.info(str(block_contents))

        # if block == DataBlockSubtype.STATUS:
        #     self.status.rocket = jsp.RocketData.from_data_block(block)
        #     return

        return ParsedBlock(block_name, block_header, block_contents)

    except NotImplementedError:
        logger.warning(
            f"Block parsing for type {block_header.message_type}, with subtype {block_header.message_subtype} not \
                implemented!"
        )
    except ValueError:
        logger.error("Invalid data block subtype")


def parse_rn2483_transmission(data: str, config: Config) -> Optional[ParsedTransmission]:
    """
    Parses RN2483 Packets and extracts our telemetry payload blocks, returns parsed transmissionobject if packet
    is valid.
    """
    # List of parsed blocks
    parsed_blocks: list[ParsedBlock] = []

    # Extract the packet header
    data = data.strip()  # Sometimes some extra whitespace
    logger.debug(f"Full data string: {data}")
    pkt_hdr = PacketHeader.from_hex(data[:32])

    if len(pkt_hdr) <= 32:  # If this packet nothing more than just the header
        logger.info(f"{pkt_hdr}")

    blocks = data[32:]  # Remove the packet header

    if not is_valid_packet_header(pkt_hdr, config.approved_callsigns):  # Return immediately if packet header is invalid
        return

    # Parse through all blocks
    while blocks != "":
        # Parse block header
        logger.debug(f"Blocks: {blocks}")
        logger.debug(f"Block header: {blocks[:8]}")
        block_header = BlockHeader.from_hex(blocks[:8])

        # Select block contents
        block_len = len(block_header) * 2  # Convert length in bytes to length in hex symbols
        block_contents = blocks[8:block_len]
        logger.debug(f"Block info: {block_header}")

        # Block Header Validity
        if not block_header.valid:
            logger.error("Block header contains invalid block type values, skipping block")
            blocks = blocks[block_len:]
            continue

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


def is_valid_packet_header(pkt_hdr: PacketHeader, approved_callsigns: dict[str, str]) -> bool:
    """Validates the packet header"""

    # Ensure packet is from an approved call sign
    if pkt_hdr.callsign in approved_callsigns:
        logger.info(f"Incoming packet from {pkt_hdr.callsign} ({approved_callsigns.get(pkt_hdr.callsign)})")
    else:
        logger.warning(f"Incoming packet from unauthorized call sign {pkt_hdr.callsign}")
        return False

    # Ensure packet version compatibility
    if pkt_hdr.version < SUPPORTED_ENCODING_VERSION:
        logger.error(f"This version of ground station does not support encoding below {SUPPORTED_ENCODING_VERSION}")
        return False

    return True
