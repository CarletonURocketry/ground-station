# # Contains test cases for verifying the parsing of block headers
# __author__ = "Elias Hawa"

import pytest
# from modules.telemetry.v1.data_block import (
#     PressureDB,
#     TemperatureDB,
#     LinearAccelerationDB,
#     AngularVelocityDB,
#     HumidityDB,
#     CoordinatesDB,
#     VoltageDB,
# )

import modules.telemetry.packet_spec.blocks as blocks

from modules.telemetry.packet_spec.headers import (
    BlockType,
    PacketHeader,
    BlockHeader,
    InvalidHeaderFieldValueError
)
from modules.telemetry.packet_spec.blocks import (
    Block,
    TimedBlock,
    Pressure,
    Temperature,
    LinearAcceleration,
    AngularVelocity,
    Humidity,
    Coordinates,
    Voltage,
    MagneticField
)


@pytest.fixture
def pressure_data_content() -> bytes:
    """
    Returns a pressure sensor reading with the following attributes
    mission time: 0 ms
    pressure: 100810 mB
    """
    
    return b"\x00\x00\xca\x89\x01\x00"


@pytest.fixture
def temperature_data_content() -> bytes:
    """
    Returns a temperature sensor reading with the following attributes
    mission time: 0 ms
    temperature: 22000 mdC
    """
    return b"\x00\x00\xf0\x55\x00\x00"


@pytest.fixture
def linear_acceleration_data_content() -> bytes:    
    #     Returns a linear acceleration sensor reading with the following attributes
    #     mission time: 0ms
    #     x axis acceleration: 3cm/s^2
    #     y axis acceleration: -4cm/s^2
    #     z axis acceleration: 1032cm/s^2
    #     Note that LinearAccelerationDB from_bytes method should convert the axis values
    #     from cm/s^2 to m/s^2
    
    return b"\x00\x00\x03\x00\xfc\xff\x08\x04"


@pytest.fixture
def angular_velocity_data_content() -> bytes:
#     """
#     Returns an angular velocity sensor reading with the following attributes
#     mission time: 0ms
#     x axis velocity: 60 tenths of a degree per second
#     y axis velocity: 110 tenths of a degree per second
#     z axis velocity -30 tenths of a degree per second
#     Note that the AngularVelocityDb from_bytes method should convert the axis values
#     from tenths of a degree per second to degrees per second
#     """
    return b"\x00\x00\x06\x00\x0b\x00\xfd\xff"


@pytest.fixture
def humidity_data_content() -> bytes:
#     """
#     Returns a humidity sensor reading with the following attributes
#     mission time: 4121ms
#     humidity: 44%
#     """
    return b"\x19\x10\x30\x11\x00\x00"


@pytest.fixture
def coordinates_data_content() -> bytes:
#     """
#     Returns a coordinates sensor reading with the following attributes
#     mission time: 3340ms
#     latitude: 0
#     longitude: 0
#     """
    return b"\x0c\x0d\x00\x00\x00\x00\x00\x00\x00\x00"


@pytest.fixture
def voltage_data_content() -> bytes:
#     """
#     Returns a voltage sensor reading with the following attributes
#     mission time: 3483 ms
#     id: 2
#     voltage: 3310 mV
#     """
    return b"\x9B\x0D\xEE\x0C\x02"


def test_pressure_data_block(pressure_data_content: bytes) -> None:
    """Test that the pressure data block is parsed correctly."""
    packet_header = PacketHeader("PressureTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.PRESSURE)
    
    # Parse block
    pressure_block = blocks.parse_block_contents(packet_header,block_header, pressure_data_content)
     
    assert (pressure_block.measurement_time == 0.0)
    assert (pressure_block.pressure == 100810)
   

# def test_temperature_data_block(temperature_data_content: bytes) -> None:
#     """Test that the temperature is parsed correctly."""
#     tdb = TemperatureDB.from_bytes(temperature_data_content)

#     assert tdb.mission_time == 0
#     assert tdb.temperature == 22000

def test_temperature_data_block(temperature_data_content: bytes) -> None:
    """Test that the temperature is parsed correctly."""
    packet_header = PacketHeader("TemperatureTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.TEMPERATURE)

    temperature_block = blocks.parse_block_contents(packet_header, block_header, temperature_data_content)
    print(temperature_block)
    assert temperature_block.measurement_time == 0
    assert temperature_block.temperature == 22000


def test_linear_acceleration_data_block(linear_acceleration_data_content: bytes) -> None:
    """Test that the linear acceleration is parsed correctly."""
    packet_header = PacketHeader("LinearAccelerationTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.LINEAR_ACCELERATION)

    linear_acceleration_block = blocks.parse_block_contents(packet_header, block_header, linear_acceleration_data_content)
    
    assert linear_acceleration_block.measurement_time == 0
    assert linear_acceleration_block.x_axis/100 == 0.03
    assert linear_acceleration_block.y_axis/100 == -0.04
    assert linear_acceleration_block.z_axis/100 == 10.32
    

def test_angular_velocity_data_block(angular_velocity_data_content: bytes) -> None:
    """Test that the angular velocity is parsed correctly."""
    packet_header = PacketHeader("AngularVelocityTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.ANGULAR_VELOCITY)
     
    ang_vel = blocks.parse_block_contents(packet_header,block_header,angular_velocity_data_content)

   
    assert ang_vel.measurement_time == 0
    assert ang_vel.x_axis/10 == 0.6
    assert ang_vel.y_axis/10 == 1.1
    assert ang_vel.z_axis/10 == -0.3


def test_humidity_data_block(humidity_data_content: bytes) -> None:
    """Test that the humidity data block is parsed correctly."""
    packet_header = PacketHeader("HumidityTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.HUMIDITY)
    hdb = blocks.parse_block_contents(packet_header, block_header, humidity_data_content)

    print(f"Raw measurement time: {hdb.measurement_time}")
    print(f"Raw humidity: {hdb.humidity}")

    #Verify the parsed measurement time in terms of seconds
    assert hdb.measurement_time == 4.12
    assert hdb.humidity == 4400


def test_coordinates_data_block(coordinates_data_content: bytes) -> None:
     """Test that the coordinates data block is parsed correctly."""
     packet_header = PacketHeader("CoordinatesTest", 0, 1, 0)
     block_header = BlockHeader(BlockType.COORDINATES)
     cdb = blocks.parse_block_contents(packet_header, block_header, coordinates_data_content)
     assert cdb.measurement_time == 3.34
     assert cdb.latitude == 0
     assert cdb.longitude == 0


def test_voltage_data_block(voltage_data_content: bytes) -> None:
    """Test that the voltage data block is parsed correctly."""
    packet_header = PacketHeader("VoltageTest", 0, 1, 0)
    block_header = BlockHeader(BlockType.VOLTAGE)
    vdb = blocks.parse_block_contents(packet_header, block_header, voltage_data_content)

    # Had to have the assertions be in decimals to account for the conversion from milliseconds to seconds
   
    assert vdb.measurement_time == 3.48
    assert vdb.identifier == 2
    assert vdb.voltage == 3310

# Running the pressure sensor parsing command. 

