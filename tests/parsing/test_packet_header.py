# Contains test cases for verifying the parsing of block headers
__author__ = "Matteo Golin"

import pytest
from modules.telemetry.v1.block import PacketHeader


@pytest.fixture
def linguini_header() -> str:
    """Returns a packet header with call sign VA3INI (Matteo Golin)"""
    return "564133494e490000000c010100000000"


@pytest.fixture
def zeta_header() -> str:
    """Returns a packet header with call sign VA3ZTA (Darwin Jull)"""
    return "5641335A54410000000A020600040000"


@pytest.fixture
def devil_header() -> str:
    """Returns a packet header with call sign VE3LWN (Thomas Selwyn)"""
    return "5645334C574E2F573568010F00000690"


def test_linguini_header(linguini_header: str) -> None:
    """Test that the linguini packet header is parsed correctly."""
    hdr = PacketHeader.from_hex(linguini_header)

    assert hdr.callsign == "VA3INI"
    assert hdr.callzone == ""
    assert len(hdr) == 52
    assert hdr.version == 1
    assert hdr.src_addr == 1
    assert hdr.packet_num == 0


def test_zeta_header(zeta_header: str) -> None:
    """Test that the zeta (Darwin) packet header is parsed correctly."""
    hdr = PacketHeader.from_hex(zeta_header)

    assert hdr.callsign == "VA3ZTA"
    assert hdr.callzone == ""
    assert len(hdr) == 44
    assert hdr.version == 2
    assert hdr.src_addr == 6
    assert hdr.packet_num == 1024


def test_devil_header(devil_header: str) -> None:
    """Test that the devils (Selwyn) packet header is parsed correctly."""
    hdr = PacketHeader.from_hex(devil_header)

    assert hdr.callsign == "VE3LWN"
    assert hdr.callzone == "W5"
    assert len(hdr) == 420
    assert hdr.version == 1
    assert hdr.src_addr == 0xF
    assert hdr.packet_num == 2416312320
