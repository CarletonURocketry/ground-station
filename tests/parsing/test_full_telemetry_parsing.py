import pytest
from modules.telemetry.v1.block import BlockHeader
from modules.telemetry.telemetry_utils import parse_radio_block


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
    assert prb.block_contents.mission_time == 0


def test_invalid_datablock_subtype_test(pkt_version: int, block_header_error: BlockHeader, hex_block_contents: str, caplog) -> None:
    """
    test for random subtype ValueError
    """
    parse_radio_block(pkt_version, block_header_error, hex_block_contents)
    assert "Invalid data block subtype" in caplog.text




