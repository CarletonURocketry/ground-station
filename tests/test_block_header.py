# # Contains test cases for verifying the parsing of block headers.

# # Imports
import pytest
# from modules.telemetry.v1.block import BlockHeader, InvalidHeaderFieldValueError
import modules.telemetry.packet_spec.headers as headers 



# # Fixtures
@pytest.fixture
def header1() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 1
    destination address: 0
    """
    return "02"


@pytest.fixture
def header2() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 2
    destination address: 0
    """
    return "00"


@pytest.fixture
def header3() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 0
    message sub type: 3
    destination address: 0
    """
    return "03"


@pytest.fixture
def header1_invalid_message_type() -> str:
    """
    Data block header with the following attributes:
    length: 12 bytes
    message type: 254
    message sub type: 1
    destination address: 0
    """
    return "fe"


@pytest.fixture
def header1_too_large() -> str:
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
    header_data = bytes.fromhex(header1)
    hdr = headers.parse_block_header(header_data)

    assert len(header_data) == 1
    assert hdr.type == headers.BlockType.TEMPERATURE
    
def test_parsing_header2(header2: str):
    """Ensure that parsing a block header works as expected."""
    header_data = bytes.fromhex(header2)
    hdr = headers.parse_block_header(header_data)

    assert len(header_data) == 1
    assert hdr.type == headers.BlockType.ALTITUDE_ABOVE_SEA_LEVEL



def test_parsing_header3(header3: str):
    """Ensure that parsing a block header works as expected."""
    header_data = bytes.fromhex(header3)
    hdr = headers.parse_block_header(header_data)

    assert len(header_data) == 1
    assert hdr.type == headers.BlockType.PRESSURE


def test_parsing_header1_invalid_message_type(header1_invalid_message_type: str):
    """Ensure that parsing a block header with an invalid message type raises an error."""
    with pytest.raises(
        headers.InvalidHeaderFieldValueError, match="Invalid BlockHeader field: fe is not a valid value for bad block header: 254 is not a valid BlockType"
    ):
        header_data = bytes.fromhex(header1_invalid_message_type)
        header = headers.parse_block_header(header_data)

def test_parsing_header1_too_large_header(header1_too_large: str):
    """Ensure that parsing a block header with an invalid message subtype raises an error."""
    with pytest.raises(
        headers.InvalidHeaderFieldValueError,
        match="Invalid BlockHeader field: 0200fe00 is not a valid value for bad block header: unpack requires a buffer of 1 bytes",
    ):
        header_data = bytes.fromhex(header1_too_large)
        header = headers.parse_block_header(header_data)



# def test_parsing_header1_invalid_message_subtype(header1_invalid_message_subtype: str):
#     """Ensure that parsing a block header with an invalid message subtype raises an error."""
#     with pytest.raises(
#         InvalidHeaderFieldValueError,
#         match="Invalid BlockHeader field: 254 is not a valid value for DataBlockSubtype",
#     ):
#         _ = BlockHeader.from_hex(header1_invalid_message_subtype)


# def test_parsing_header1_invalid_destination(header1_invalid_destination: str):
#     """Ensure that parsing a block header an invalid destination raises an error."""
#     with pytest.raises(
#         InvalidHeaderFieldValueError, match="Invalid BlockHeader field: 5 is not a valid value for DeviceAddress"
#     ):
#         _ = BlockHeader.from_hex(header1_invalid_destination)
