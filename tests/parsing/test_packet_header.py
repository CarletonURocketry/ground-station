# Contains test cases for verifying the parsing of block headers
__author__ = "Matteo Golin"

import pytest
from modules.telemetry.telemetry_utils import parse_packet_header


@pytest.fixture
def linguini_header() -> str:
    """Returns a packet header with call sign VA3INI (Matteo Golin)"""
    return "564133494E49140090070000"


@pytest.fixture
def zeta_header() -> str:
    """Returns a packet header with call sign VA3ZTA (Darwin Jull)"""
    return "5641335A5441090064000000"


def test_linguini_header(linguini_header: str) -> None:
    """Test that the linguini packet header is parsed correctly."""
    callsign, length, ver, src_addr, packet_num = parse_packet_header(linguini_header)

    assert callsign == "VA3INI"
    assert length == 24
    assert ver == 0
    assert src_addr == 9
    assert packet_num == 7


def test_zeta_header(zeta_header: str) -> None:
    """Test that the zeta (Darwin) packet header is parsed correctly."""
    callsign, length, ver, src_addr, packet_num = parse_packet_header(zeta_header)

    assert callsign == "VA3ZTA"
    assert length == 12
    assert ver == 8
    assert src_addr == 6
    assert packet_num == 1024
