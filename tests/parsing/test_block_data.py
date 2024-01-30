# Contains test cases for verifying the parsing of block headers
__author__ = "Elias Hawa"

import pytest
from modules.telemetry.v1.data_block import PressureDB


@pytest.fixture
def pressure_data_content() -> bytes:
    """Returns a pressure sensor reading with the following attributes
    mission time: 0
    pressure: 100810"""
    return b"\x00\x00\x00\x00\xca\x89\x01\x00"


def test_pressure_data_block(pressure_data_content: bytes) -> None:
    """Test that the linguini packet header is parsed correctly."""
    pdb = PressureDB.from_bytes(pressure_data_content)

    assert pdb.mission_time == 0
    assert pdb.pressure == 100810
