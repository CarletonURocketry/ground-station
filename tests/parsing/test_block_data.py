# Contains test cases for verifying the parsing of block headers
__author__ = "Elias Hawa"

import pytest
from modules.telemetry.v1.data_block import (
    PressureDB,
    TemperatureDB,
    LinearAccelerationDB,
    AngularVelocityDB,
    HumidityDB,
    CoordinatesDB,
    VoltageDB,
)


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


@pytest.fixture
def linear_acceleration_data_content() -> bytes:
    """
    Returns a linear acceleration sensor reading with the following attributes
    mission time: 0ms
    x axis acceleration: 3cm/s^2
    y axis acceleration: -4cm/s^2
    z axis acceleration: 1032cm/s^2
    Note that LinearAccelerationDB from_bytes method should convert the axis values
    from cm/s^2 to m/s^2
    """
    return b"\x00\x00\x00\x00\x03\x00\xfc\xff\x08\x04\x00\x00"


@pytest.fixture
def angular_velocity_data_content() -> bytes:
    """
    Returns an angular velocity sensor reading with the following attributes
    mission time: 0ms
    x axis velocity: 60 tenths of a degree per second
    y axis velocity: 110 tenths of a degree per second
    z axis velocity -30 tenths of a degree per second
    Note that the AngularVelocityDb from_bytes method should convert the axis values
    from tenths of a degree per second to degrees per second
    """
    return b"\x00\x00\x00\x00\x06\x00\x0b\x00\xfd\xff\x00\x00"


@pytest.fixture
def humidity_data_content() -> bytes:
    """
    Returns a humidity sensor reading with the following attributes
    mission time: 4121ms
    humidity: 44%
    """
    return b"\x19\x10\x00\x00\xfe\x10\x00\x00"


@pytest.fixture
def coordinates_data_content() -> bytes:
    """
    Returns a coordinates sensor reading with the following attributes
    mission time: 3340ms
    latitude: 0
    longitude: 0
    """
    return b"\x0c\x0d\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


@pytest.fixture
def voltage_data_content() -> bytes:
    """
    Returns a voltage sensor reading with the following attributes
    mission time: 3483 ms
    id: 2
    voltage: 3310 mV
    """
    return b"\x9b\x0d\x00\x00\x02\x00\xee\x0c"


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


def test_linear_acceleration_data_block(linear_acceleration_data_content: bytes) -> None:
    """Test that the linear acceleration is parsed correctly."""
    lin_acc = LinearAccelerationDB.from_bytes(linear_acceleration_data_content)

    assert lin_acc.mission_time == 0
    assert lin_acc.x_axis == 0.03
    assert lin_acc.y_axis == -0.04
    assert lin_acc.z_axis == 10.32
    assert lin_acc.magnitude == 10.32


def test_angular_velocity_data_block(angular_velocity_data_content: bytes) -> None:
    """Test that the angular velocity is parsed correctly."""
    ang_vel = AngularVelocityDB.from_bytes(angular_velocity_data_content)

    assert ang_vel.mission_time == 0
    assert ang_vel.x_axis == 0.6
    assert ang_vel.y_axis == 1.1
    assert ang_vel.z_axis == -0.3
    assert ang_vel.magnitude == 1.29


def test_humidity_data_block(humidity_data_content: bytes) -> None:
    """Test that the humidity data block is parsed correctly."""
    hdb = HumidityDB.from_bytes(humidity_data_content)

    assert hdb.mission_time == 4121
    assert hdb.humidity == 4350


def test_coordinates_data_block(coordinates_data_content: bytes) -> None:
    """Test that the coordinates data block is parsed correctly."""
    cdb = CoordinatesDB.from_bytes(coordinates_data_content)

    assert cdb.mission_time == 3340
    assert cdb.latitude == 0
    assert cdb.longitude == 0


def test_voltage_data_block(voltage_data_content: bytes) -> None:
    """Test that the voltage data block is parsed correctly."""
    vdb = VoltageDB.from_bytes(voltage_data_content)

    assert vdb.mission_time == 3483
    assert vdb.id == 2
    assert vdb.voltage == 3310
