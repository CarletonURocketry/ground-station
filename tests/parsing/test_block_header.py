# Contains test cases for verifying the parsing of block headers.

# Imports
import pytest
from modules.telemetry.block import BlockHeader


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
    hdr = BlockHeader.from_hex(header1)

    assert len(hdr) == 20
    assert hdr.has_crypto is False
    assert hdr.message_type == 2
    assert hdr.message_subtype == 3
    assert hdr.destination == 0


def test_parsing_header2(header2: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header2)

    assert len(hdr) == 8
    assert hdr.has_crypto == 0
    assert hdr.message_type == 0
    assert hdr.message_subtype == 0
    assert hdr.destination == 0xF


def test_parsing_header3(header3: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header3)

    assert len(hdr) == 20
    assert hdr.has_crypto == 0
    assert hdr.message_type == 2
    assert hdr.message_subtype == 1
    assert hdr.destination == 0
