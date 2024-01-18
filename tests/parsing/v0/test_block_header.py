# Contains test cases for verifying the parsing of block headers.
__author__ = "Matteo Golin"

# Imports
import pytest
from modules.telemetry.telemetry_utils import parse_block_header
from modules.telemetry.block import RadioBlockType, DataBlockSubtype, ControlBlockSubtype
from modules.telemetry.block import DeviceAddress


# Fixtures
@pytest.fixture
def altitude_header() -> str:
    """Hex data for an altitude data block header."""
    return "840C0000"


@pytest.fixture
def signal_report_header() -> str:
    """Hex data for a signal report control block header."""
    return "01000F20"


@pytest.fixture
def status_header() -> str:
    """Hex data for a status data block header."""
    return "84040000"


# Tests
def test_altitude_header(altitude_header: str):
    """Ensure that parsing an altitude data block header works as expected."""
    len, sig, msg_type, msg_subtype, destaddr = parse_block_header(altitude_header)

    assert len == 20
    assert sig == 0
    assert RadioBlockType(msg_type) == RadioBlockType.DATA
    assert DataBlockSubtype(msg_subtype) == DataBlockSubtype.ALTITUDE
    assert DeviceAddress(destaddr) == DeviceAddress.GROUND_STATION


def test_signal_report_header(signal_report_header: str):
    """Ensure that parsing a signal report control block header works as expected."""
    _, sig, msg_type, msg_subtype, destaddr = parse_block_header(signal_report_header)

    # assert _ == 8  # Not sure about this length
    assert sig == 0
    assert RadioBlockType(msg_type) == RadioBlockType.CONTROL
    assert ControlBlockSubtype(msg_subtype) == ControlBlockSubtype.SIGNAL_REPORT
    assert DeviceAddress(destaddr) == DeviceAddress.MULTICAST


def test_test_header(status_header: str):
    """Ensure that parsing a status data block header works as expected."""
    len, sig, msg_type, msg_subtype, destaddr = parse_block_header(status_header)

    assert len == 20
    assert sig == 0
    assert RadioBlockType(msg_type) == RadioBlockType.DATA
    assert DataBlockSubtype(msg_subtype) == DataBlockSubtype.STATUS
    assert DeviceAddress(destaddr) == DeviceAddress.GROUND_STATION
