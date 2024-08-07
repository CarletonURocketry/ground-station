import pytest
import logging
from pytest import LogCaptureFixture
from modules.telemetry.v1.block import (
    BlockType,
    PacketHeader,
    BlockHeader,
    InvalidHeaderFieldValueError,
    UnsupportedEncodingVersionError,
)
from modules.telemetry.parsing_utils import parse_radio_block, from_approved_callsign
from modules.misc.config import load_config
from modules.telemetry.v1.data_block import DataBlockSubtype

# Fixtures and tests to ensure that parse_radio_block works as expected


@pytest.fixture
def pkt_version() -> int:
    """
    returns the packet version as an integer:
    """
    return 192


@pytest.fixture
def block_header() -> BlockHeader:
    """
    returns a blockheader
    """
    return BlockHeader.from_hex("02000300")


@pytest.fixture
def hex_block_contents() -> str:
    """
    returns the contents
    """
    return "00000000f0c30000"


def test_radio_block(pkt_version: int, block_header: BlockHeader, hex_block_contents: str) -> None:
    """
    test a proper line on parse_radio_block
    """
    prb = parse_radio_block(pkt_version, block_header, hex_block_contents)
    assert prb is not None
    assert prb.block_header.length == 12
    assert prb.block_header.message_type == BlockType.DATA.value
    assert prb.block_header.message_subtype == DataBlockSubtype.TEMPERATURE.value
    assert prb.block_header.destination == 0
    assert prb.block_name == "temperature"
    assert prb.block_contents["mission_time"] == 0


# Fixtures and tests to ensure that parse_radio_block handles errors as expected


@pytest.fixture
def not_implemented_datablock_subtype() -> BlockHeader:
    return BlockHeader.from_hex("02000a00")


def test_invalid_datablock_subtype(pkt_version: int, hex_block_contents: str):
    """
    test for random subtype ValueError
    """
    # subtype is 154, thus non-existent
    with pytest.raises(
        InvalidHeaderFieldValueError, match="Invalid BlockHeader field: 154 is not a valid value for DataBlockSubtype"
    ):
        parse_radio_block(pkt_version, BlockHeader.from_hex("02009A00"), hex_block_contents)


config = load_config("config.json")

# Fixtures and tests to ensure that from_approved_callsign works as expected


@pytest.fixture
def approved_callsigns() -> dict[str, str]:
    return config.approved_callsigns


@pytest.fixture
def valid_packet_header() -> PacketHeader:
    # first 32 characters of a packet
    hdr = "564133494e490000000c010137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


@pytest.fixture
def non_approved_callsign() -> PacketHeader:
    hdr = "52415454204D4F53530c010137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


# Test valid header
def test_is_approved_pkt_hdr(
    valid_packet_header: PacketHeader, approved_callsigns: dict[str, str], caplog: LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    assert from_approved_callsign(valid_packet_header, approved_callsigns)
    assert (
        f"Incoming packet from {valid_packet_header.callsign} ({approved_callsigns.get(valid_packet_header.callsign)})"
        in caplog.text
    )


# Test an invalid header: unapproved call sign
def test_is_unauthorized_callsign(
    non_approved_callsign: PacketHeader, approved_callsigns: dict[str, str], caplog: LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    assert not from_approved_callsign(non_approved_callsign, approved_callsigns)
    assert f"Incoming packet from unauthorized call sign {non_approved_callsign.callsign}" in caplog.text


# Test an invalid header: version number 0
def test_is_invalid_hdr(approved_callsigns: dict[str, str]) -> None:
    hdr = "564133494e490000000c000137000000"
    with pytest.raises(UnsupportedEncodingVersionError, match="Unsupported encoding version: 0"):
        PacketHeader.from_hex(hdr)


# Test an invalid header: non approved callsign and incorrect version number
def test_is_invalid_hdr2(approved_callsigns: dict[str, str]) -> None:
    hdr = "52415454204D4F53530c0b0137000000"

    with pytest.raises(UnsupportedEncodingVersionError, match="Unsupported encoding version: 11"):
        PacketHeader.from_hex(hdr)
