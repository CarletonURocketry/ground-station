import pytest
from modules.telemetry.telemetry_utils import parse_rn2483_transmission, parse_radio_block, is_valid_packet_header, ParsedTransmission
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
def non_valid_packet() -> PacketHeader:
    # changed e in valid pakct header fixture to a 2
    hdr = "5641334942490000000c010137000000"
    # --------------^ this character
    pkt_hdr = PacketHeader.from_hex(hdr) 
    return pkt_hdr
# Tests

def test_is_valid_hdr(valid_packet_header: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert is_valid_packet_header(valid_packet_header, approved_callsigns) == True

def test_is_non_valid_hdr(non_valid_packet: PacketHeader, approved_callsigns: dict[str, str]) -> None:
    assert is_valid_packet_header(non_valid_packet, approved_callsigns) == False