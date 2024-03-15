import pytest
from modules.telemetry.v1.block import BlockHeader
from modules.telemetry.telemetry_utils import parse_radio_block
from modules.telemetry.telemetry_utils import is_valid_packet_header
from modules.telemetry.v1.block import PacketHeader
from modules.misc.config import load_config

LINE1 = "564133494e490000000c0101010000000200020000000000ac5d00000200030000000000f0c300000200030000000000f0c30000"


@pytest.fixture
def pkt_version() -> int:
    """
    returns the packet version as an integer
    """

    return int("0x" + LINE1[19:21], 16)


@pytest.fixture
def block_header() -> BlockHeader:
    """
    returns a blockheader
    """

    return BlockHeader.from_hex(LINE1[32:40])


@pytest.fixture
def hex_block_contents() -> str:
    """
    returns the contents
    """
    return LINE1[-16:]


@pytest.fixture
def block_header_error() -> BlockHeader:
    """
    Invalid data block subtype, random non-existant
    """

    bad_header = BlockHeader.from_hex(LINE1[32:40])
    bad_header.message_subtype = int("0x" + "9A", 16)
    # cannot reach to the NotImplementedError
    return bad_header


def test_radio_block(pkt_version: int, block_header: BlockHeader, hex_block_contents:str) -> None:
    """
    test a proper line on parse_radio_block
    """
    prb = parse_radio_block(1, block_header, hex_block_contents)
    assert prb.block_header.length == 12
    assert prb.block_header.message_type == 0
    assert prb.block_header.message_subtype == 2
    assert prb.block_header.destination == 0
    assert prb.block_header.valid is True
    assert prb.block_name == 'temperature'
    assert prb.block_contents['mission_time'] == 0


def test_invalid_datablock_subtype_test(pkt_version: int, block_header_error: BlockHeader, hex_block_contents: str, caplog) -> None:
    """
    test for random subtype ValueError
    """
    parse_radio_block(pkt_version, block_header_error, hex_block_contents)
    assert "Invalid data block subtype" in caplog.text





config = load_config("config.json")

# Fixtures


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


@pytest.fixture
def version_num_zero() -> PacketHeader:
    hdr = "564133494e490000000c000137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


@pytest.fixture
def invalid_packet_header() -> PacketHeader:
    hdr = "52415454204D4F53530c0b0137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


# Tests


# Test valid header
def test_is_valid_hdr(valid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert is_valid_packet_header(valid_packet_header, approved_callsigns)


# Test a invalid header: unapproved call sign
def test_is_invalid_hdr1(non_approved_callsign: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(non_approved_callsign, approved_callsigns))


# Test invalid header: version number 0
def test_is_invalid_hdr2(version_num_zero: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(version_num_zero, approved_callsigns))


# Test invalid header: non approved callsign and incorrect version number
def test_is_invalid_hdr3(invalid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(invalid_packet_header, approved_callsigns))
