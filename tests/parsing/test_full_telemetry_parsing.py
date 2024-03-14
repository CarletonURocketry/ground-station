import pytest
from modules.telemetry.telemetry_utils import is_valid_packet_header
from modules.telemetry.v1.block import PacketHeader
from modules.misc.config import load_config


config = load_config("config.json")

# Fixtures


@pytest.fixture
def approved_callsigns() -> dict[str, str]:
    return config.approved_callsigns


@pytest.fixture
def valid_packet_header() -> PacketHeader:
    # first 32 characters of a packet
    hdr = "564133494e490000000c010137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


@pytest.fixture
def non_approved_callsign() -> PacketHeader:
    hdr = "52415454204D4F53530c010137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


@pytest.fixture
def version_num_zero() -> PacketHeader:
    hdr = "564133494e490000000c000137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


@pytest.fixture
def invalid_packet_header() -> PacketHeader:
    hdr = "52415454204D4F53530c0b0137000000"
    pkt_hdr = PacketHeader.from_hex(hdr)
    return pkt_hdr


# Tests


# Test valid header
def test_is_valid_hdr(valid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert is_valid_packet_header(valid_packet_header, approved_callsigns)


# Test a invalid header: unapproved call sign
def test_is_invalid_hdr1(non_approved_callsign: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(non_approved_callsign, approved_callsigns))


# Test invalid header: version number 0
def test_is_invalid_hdr2(version_num_zero: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(version_num_zero, approved_callsigns))


# Test invalid header: non approved callsign and incorrect version number
def test_is_invalid_hdr3(invalid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert not (is_valid_packet_header(invalid_packet_header, approved_callsigns))
