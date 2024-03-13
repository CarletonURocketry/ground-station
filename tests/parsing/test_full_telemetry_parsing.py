import logging

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

    block_length = int("0x" + LINE1[32:34], 16)
    block_type = int("0x" + LINE1[34:36], 16)
    subtype = int("0x" + LINE1[36:38], 16)
    address = int("0x" + LINE1[38:40], 16)
    return BlockHeader(block_length, block_type, subtype, address)


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
    block_length = int("0x" + LINE1[32:34], 16)
    block_type = int("0x" + LINE1[34:36], 16)
    subtype = int("0x" + "9A", 16)
    address = int("0x" + LINE1[38:40], 16)
    # cannot reach to the NotImplementedError
    return BlockHeader(block_length, block_type, subtype, address)


def test_radio_block(pkt_version: int, block_header: BlockHeader, hex_block_contents:str) -> None:
    prb = parse_radio_block(1, block_header, hex_block_contents)
    assert prb.block_header.length == 2
    assert prb.block_header.message_type == 0
    assert prb.block_header.message_subtype == 2
    assert prb.block_header.destination == 0
    assert prb.block_header.valid == True
    assert prb.block_name == 'temperature'
    assert prb.block_contents.mission_time == 0


def test_invalid_datablock_subtype_test(pkt_version: int, block_header_error: BlockHeader, hex_block_contents: str, caplog) -> None:
    """
    test for random subtype ValueError
    """
    parse_radio_block(pkt_version, block_header_error, hex_block_contents)
    assert "Invalid data block subtype" in caplog.text




