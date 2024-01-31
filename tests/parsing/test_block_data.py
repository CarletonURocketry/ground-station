# Contains test cases for verifying the parsing of block headers
__author__ = "Elias Hawa"

import pytest
from modules.telemetry.v1.data_block import PressureDB
from modules.telemetry.v1.data_block import TemperatureDB


@pytest.fixture
def pressure_data_content() -> bytes:
    """
    Returns a pressure sensor reading with the following attributes
    mission time: 0 ms
    pressure: 100810 mB
    """
    return b"\x00\x00\x00\x00\xca\x89\x01\x00"


@pytest.fixture
def temperature_data_content() -> bytes:
    """
    Returns a temperature sensor reading with the following attributes
    mission time: 0 ms
    temperature: 22000 mdC
    """
    return b"\x00\x00\x00\x00\xf0\x55\x00\x00"


def test_pressure_data_block(pressure_data_content: bytes) -> None:
    """Test that the pressure data block is parsed correctly."""
    pdb = PressureDB.from_bytes(pressure_data_content)

    assert pdb.mission_time == 0
    assert pdb.pressure == 100810


def test_temperature_data_block(temperature_data_content: bytes) -> None:
    """Test that the temperature is parsed correctly."""
    tdb = TemperatureDB.from_bytes(temperature_data_content)

    assert tdb.mission_time == 0
    assert tdb.temperature == 22000
