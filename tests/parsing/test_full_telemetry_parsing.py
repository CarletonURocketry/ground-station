import pytest
from modules.telemetry.v1.block import PacketHeader, BlockHeader, InvalidHeaderFieldValueError
from modules.telemetry.telemetry_utils import parse_radio_block, is_approved_packet_header
from modules.misc.config import load_config


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
    return BlockHeader.from_hex("02000200")


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
    if prb is not None:
        assert prb.block_header.length == 12
        assert prb.block_header.message_type == 0
        assert prb.block_header.message_subtype == 2
        assert prb.block_header.destination == 0
        assert prb.block_name == "temperature"
        assert prb.block_contents["mission_time"] == 0


# fixtures


@pytest.fixture
def not_implemented_datablock_subtype() -> BlockHeader:
    return BlockHeader.from_hex("02000400")


def test_invalid_datablock_subtype(pkt_version: int, hex_block_contents: str):
    """
    test for random subtype ValueError
    """
    # subtype is 154, thus non-existent
    with pytest.raises(
        InvalidHeaderFieldValueError, match="Invalid BlockHeader field: 154 is not a valid value for DataBlockSubtype"
    ):
        parse_radio_block(pkt_version, BlockHeader.from_hex("02009A00"), hex_block_contents)


def test_not_implemented_error(
    pkt_version: int, not_implemented_datablock_subtype: BlockHeader, hex_block_contents: str
) -> None:
    """
    test for a subtye that exists but is not implemented
    """
    assert parse_radio_block(pkt_version, not_implemented_datablock_subtype, hex_block_contents) is None


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
    assert is_approved_packet_header(valid_packet_header, approved_callsigns) is None


# Test a invalid header: unapproved call sign
# def test_is_invalid_hdr1(non_approved_callsign: PacketHeader, approved_callsigns: dict[str, str]) -> None:
#     assert not (is_approved_packet_header(non_approved_callsign, approved_callsigns))


# # Test invalid header: version number 0
# def test_is_invalid_hdr2(version_num_zero: PacketHeader, approved_callsigns: dict[str, str]) -> None:
#     assert not (is_approved_packet_header(version_num_zero, approved_callsigns))


# # Test invalid header: non approved callsign and incorrect version number
# def test_is_invalid_hdr3(invalid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
#     assert not (is_approved_packet_header(invalid_packet_header, approved_callsigns))
