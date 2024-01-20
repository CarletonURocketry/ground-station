# Contains test cases for verifying the parsing of block headers
__author__ = "Matteo Golin"

import pytest
from modules.telemetry.block import PacketHeader


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
    hdr = PacketHeader.from_hex(linguini_header)

    assert hdr.callsign == "VA3INI"
    assert len(hdr) == 24
    assert hdr.version == 0
    assert hdr.src_addr == 9
    assert hdr.packet_num == 7


def test_zeta_header(zeta_header: str) -> None:
    """Test that the zeta (Darwin) packet header is parsed correctly."""
    hdr = PacketHeader.from_hex(zeta_header)

    assert hdr.callsign == "VA3ZTA"
    assert len(hdr) == 12
    assert hdr.version == 8
    assert hdr.src_addr == 6
    assert hdr.packet_num == 1024
