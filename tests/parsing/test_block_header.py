# Contains test cases for verifying the parsing of block headers.

# Imports
import pytest
from modules.telemetry.v1.block import BlockHeader


# Fixtures
@pytest.fixture
def header1() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 1
    destination address: 0
    """
    return "02000100"


@pytest.fixture
def header2() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 2
    destination address: 0
    """
    return "02000200"


@pytest.fixture
def header3() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 3
    destination address: 0
    """
    return "02000300"


def test_parsing_header1(header1: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header1)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 1
    assert hdr.destination == 0
    assert hdr.valid == True


def test_parsing_header2(header2: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header2)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 2
    assert hdr.destination == 0
    assert hdr.valid == True


def test_parsing_header3(header3: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header3)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 3
    assert hdr.destination == 0
    assert hdr.valid == True
