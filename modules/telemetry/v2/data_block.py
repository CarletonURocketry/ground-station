from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self, Type
from enum import IntEnum, Enum
from dataclasses import dataclass
import struct

from modules.misc.converter import metres_to_feet, milli_degrees_to_celsius, pascals_to_psi
import * from block

@dataclass
class Block(ABC):
    measurement_time: int

@dataclass
class AltitudeAboveLaunchLevel(Block):
    altitude: int
    
@dataclass
class AltitudeAboveSeaLevel(Block):
    altitude: int

@dataclass
class LinearAcceleration(Block):
    x_axis: int
    y_axis: int
    z_axis: int

@dataclass
class AngularVelocity(Block):
    x_axis: int
    y_axis: int
    z_axis: int

@dataclass
class Coordinates(Block):
    latitude: int
    longitude: int

@dataclass
class Humidity(Block):
    humidity: int

@dataclass
class Pressure(Block):
    pressure: int

@dataclass
class Temperature(Block):
    temperature: int

@dataclass
class Voltage(Block):
    voltage: int
    id: int

#Get the timestamp from the base timestamp
def get_timestamp(packet_header: PacketHeader, offset_timestamp: int) -> int:
    base_timestamp = packet_header.timestamp
    return base_timestamp + offset_timestamp

#Parsing the packet message
def parse_packet_message(packet_header: PacketHeader, block_header: BlockHeader, message: bytes):
    match block_header.type:
        case BlockType.ALTITUDE_ABOVE_SEA_LEVEL:
            offset_timestamp, altitude = struct.unpack("<Hi", message)
            return AltitudeAboveSeaLevel(get_timestamp(packet_header, offset_timestamp), altitude)

        case BlockType.ALTITUDE_ABOVE_LAUNCH_LEVEL:
            offset_timestamp, altitude = struct.unpack("<Hi", message)
            return AltitudeAboveLaunchLevel(get_timestamp(packet_header, offset_timestamp), altitude)

        case BlockType.TEMPERATURE:
            offset_timestamp, temperature = struct.unpack("<Hi", message)
            return Temperature(get_timestamp(packet_header, offset_timestamp), temperature)

        case BlockType.PRESSURE:
            offset_timestamp, pressure = struct.unpack("<HI", message)
            return Pressure(get_timestamp(packet_header, offset_timestamp), pressure)

        case BlockType.LINEAR_ACCLERATION:
            offset_timestamp, x_axis, y_axis, z_axis = struct.unpack("<HHHH", message)
            return LinearAcceleration(get_timestamp(packet_header, offset_timestamp), x_axis, y_axis, z_axis)

        case BlockType.ANGULAR_VELOCITY:
            offset_timestamp, x_axis, y_axis, z_axis = struct.unpack("<HHHH", message)
            return AngularVelocity(get_timestamp(packet_header, offset_timestamp), x_axis, y_axis, z_axis)

        case BlockType.HUMIDITY:
            offset_timestamp, humidity = struct.unpack("<HI", message)
            return Humidity(get_timestamp(packet_header, offset_timestamp), humidity)

        case BlockType.VOLTAGE:
            offset_timestamp, voltage = struct.unpack("<HiB", message)
            return Voltage(get_timestamp(packet_header, offset_timestamp), voltage)

        case BlockType.COORDINATES:
            offset_timestamp, latitude, longitude = struct.unpack("<Hii", message)
            return Coordinates(get_timestamp(packet_header, offset_timestamp), latitude, longitude)
