from dataclasses import dataclass, fields
from struct import unpack
from typing import ClassVar

SENSOR_ACCEL = 0
SENSOR_GYRO = 1
SENSOR_MAG = 2
SENSOR_GNSS = 3
SENSOR_ALT = 4
SENSOR_BARO = 5
STATUS_MESSAGE = 6
ERROR_MESSAGE = 7

ENUM_SIZE = 1

@dataclass
class SensorAccel:
    FORMAT: ClassVar[str] = "<Qffff"
    SIZE: ClassVar[int] = 24
    timestamp: int
    x: float
    y: float
    z: float
    temperature: float

@dataclass
class SensorGyro:
    FORMAT: ClassVar[str] = "<Qffff"
    SIZE: ClassVar[int] = 24
    timestamp: int
    x: float
    y: float
    z: float
    temperature: float

@dataclass
class SensorMag:
    FORMAT: ClassVar[str] = "<Qffffi4x"
    SIZE: ClassVar[int] = 32
    timestamp: int
    x: float
    y: float
    z: float
    temperature: float
    status: int

@dataclass
class SensorGnss:
    FORMAT: ClassVar[str] = "<QQfffffffffffII4x"
    SIZE: ClassVar[int] = 72
    timestamp: int
    time_utc: int
    latitude: float
    longitude: float
    altitude: float
    altitude_ellipsoid: float
    eph: float
    epv: float
    hdop: float
    pdop: float
    vdop: float
    ground_speed: float
    course: float
    satellites_used: int
    firmware_ver: int

@dataclass
class FusionAltitude:
    FORMAT: ClassVar[str] = "<Qf4x"
    SIZE: ClassVar[int] = 16
    timestamp: int
    altitude: float

@dataclass
class SensorBaro:
    FORMAT: ClassVar[str] = "<Qff"
    SIZE: ClassVar[int] = 16
    timestamp: int
    pressure: float
    temperature: float

@dataclass
class StatusMessage:
    FORMAT: ClassVar[str] = "<QI4x"
    SIZE: ClassVar[int] = 16
    timestamp: int
    status_code: int

@dataclass
class ErrorMessage:
    FORMAT: ClassVar[str] = "<QII"
    SIZE: ClassVar[int] = 16
    timestamp: int
    proc_id: int
    error_code: int

SCHEMAS = {
    SENSOR_ACCEL: ("accel", SensorAccel),
    SENSOR_GYRO: ("gyro", SensorGyro),
    SENSOR_MAG: ("mag", SensorMag),
    SENSOR_GNSS: ("gnss", SensorGnss),
    SENSOR_ALT: ("alt", FusionAltitude),
    SENSOR_BARO: ("baro", SensorBaro),
    STATUS_MESSAGE: ("status", StatusMessage),
    ERROR_MESSAGE: ("error", ErrorMessage),
}

def parse_block(data: bytes):
    sensor_type = data[0]
    if sensor_type not in SCHEMAS:
        raise ValueError(f"Unknown sensor type: {sensor_type}")
    _, cls = SCHEMAS[sensor_type]
    return sensor_type, cls(*unpack(cls.FORMAT, data[ENUM_SIZE:]))

def field_names(cls):
    return [f.name for f in fields(cls)]

def field_values(obj):
    return [getattr(obj, f.name) for f in fields(obj)]
