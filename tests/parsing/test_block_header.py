# Contains test cases for verifying the parsing of block headers.

# Imports
import pytest
from modules.telemetry.v1.block import BlockHeader, InvalidHeaderFieldValueError


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


@pytest.fixture
def header1_invalid_message_type() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 254
    message sub type: 1
    destination address: 0
    """
    return "02fe0100"


@pytest.fixture
def header1_invalid_message_subtype() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 254
    destination address: 0
    """
    return "0200fe00"


@pytest.fixture
def header1_invalid_destination() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 1
    destination address: 5
    """
    return "02000105"


def test_parsing_header1(header1: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header1)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 1
    assert hdr.destination == 0


def test_parsing_header2(header2: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header2)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 2
    assert hdr.destination == 0


def test_parsing_header3(header3: str):
    """Ensure that parsing a block header works as expected."""
    hdr = BlockHeader.from_hex(header3)

    assert len(hdr) == 12
    assert hdr.message_type == 0
    assert hdr.message_subtype == 3
    assert hdr.destination == 0


def test_parsing_header1_invalid_message_type(header1_invalid_message_type: str):
    """Ensure that parsing a block header with an invalid message type raises an error."""
    with pytest.raises(
        InvalidHeaderFieldValueError, match="Invalid BlockHeader field: 254 is not a valid value for BlockType"
    ):
        _ = BlockHeader.from_hex(header1_invalid_message_type)


def test_parsing_header1_invalid_message_subtype(header1_invalid_message_subtype: str):
    """Ensure that parsing a block header with an invalid message subtype raises an error."""
    with pytest.raises(
        InvalidHeaderFieldValueError,
        match="Invalid BlockHeader field: 254 is not a valid value for DataBlockSubtype",
    ):
        _ = BlockHeader.from_hex(header1_invalid_message_subtype)


def test_parsing_header1_invalid_destination(header1_invalid_destination: str):
    """Ensure that parsing a block header an invalid destination raises an error."""
    with pytest.raises(
        InvalidHeaderFieldValueError, match="Invalid BlockHeader field: 5 is not a valid value for DeviceAddress"
    ):
        _ = BlockHeader.from_hex(header1_invalid_destination)
