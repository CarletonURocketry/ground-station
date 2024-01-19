# Contains test cases for verifying the parsing of block headers.

# Imports
import pytest
from modules.telemetry.telemetry_utils import parse_block_header
from modules.telemetry.block import RadioBlockType, DataBlockSubtype, ControlBlockSubtype
from modules.telemetry.block import DeviceAddress


# Fixtures
@pytest.fixture
def header1() -> str:
    """
    Data block header with the following attributes:
    length: 20 bytes
    cryptographic signature: false
    message type: 2
    message sub type: 3
    destination address: 0
    """
    return "840C0000"


@pytest.fixture
def header2() -> str:
    """
    Data block header with the following attributes:
    length: 8 bytes
    cryptographic signature: false
    message type: 0
    message sub type: 0
    destination address: 0xF
    """
    return "01000F20"


@pytest.fixture
def header3() -> str:
    """
    Data block header with the following attributes:
    length: 20 bytes
    cryptographic signature: false
    message type: 2
    message sub type: 1
    destination address: 0
    """
    return "84040000"


def test_parsing_header1(header1: str):
    """Ensure that parsing a block header works as expected."""
    len, sig, msg_type, msg_subtype, destaddr = parse_block_header(header1)

    assert len == 20
    assert sig == 0
    assert msg_type == 2
    assert msg_subtype == 3
    assert destaddr == 0


def test_parsing_header2(header2: str):
    """Ensure that parsing a block header works as expected."""
    len, sig, msg_type, msg_subtype, destaddr = parse_block_header(header2)

    assert len == 8
    assert sig == 0
    assert msg_type == 0
    assert msg_subtype == 0
    assert destaddr == 0xF


def test_parsing_header3(header3: str):
    """Ensure that parsing a block header works as expected."""
    len, sig, msg_type, msg_subtype, destaddr = parse_block_header(header3)

    assert len == 20
    assert sig == 0
    assert msg_type == 2
    assert msg_subtype == 1
    assert destaddr == 0
