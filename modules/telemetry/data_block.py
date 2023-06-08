# Data Block classes for radio transmission payload packets.
#
# Authors:
# Samuel Dewan
# Thomas Selwyn (Devil)
# Matteo Golin

from __future__ import annotations
import struct
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Self, Type
from modules.telemetry.block import DataBlockSubtype, BlockException, BlockUnknownException
from modules.misc import converter


class DataBlockException(BlockException):
    pass


class DataBlockUnknownException(BlockUnknownException):
    pass


class DataBlock(ABC):
    """Interface for all telemetry data blocks."""

    def __init__(self, subtype: DataBlockSubtype, mission_time: int):
        self.mission_time: int = mission_time
        self.subtype: DataBlockSubtype = subtype

    def __len__(self) -> int:
        """Returns the length of the datablock, not including the header."""
        return 0

    @abstractmethod
    def to_payload(self) -> bytes:
        """Marshal block to a bytes object."""

    @abstractmethod
    @classmethod
    def from_payload(cls, payload: bytes) -> Type[Self]:
        """Returns a DataBlock initialized from a payload of bytes."""

    @staticmethod
    def parse(block_subtype: DataBlockSubtype, payload: bytes) -> Type[DataBlock]:
        """Unmarshal a bytes object to appropriate block class."""

        SUBTYPE_CLASSES: dict[DataBlockSubtype, Type[DataBlock]] = {
            DataBlockSubtype.DEBUG_MESSAGE: DebugMessageDataBlock,
            DataBlockSubtype.STATUS: StatusDataBlock,
            DataBlockSubtype.STARTUP_MESSAGE: StartupMessageDataBlock,
            DataBlockSubtype.ALTITUDE: AltitudeDataBlock,
            DataBlockSubtype.ACCELERATION: AccelerationDataBlock,
            DataBlockSubtype.GNSS: GNSSLocationBlock,
            DataBlockSubtype.GNSS_META: GNSSMetadataBlock,
            DataBlockSubtype.MPU9250_IMU: MPU9250IMUDataBlock,
            DataBlockSubtype.KX134_1211_ACCEL: KX134AccelerometerDataBlock,
            DataBlockSubtype.ANGULAR_VELOCITY: AngularVelocityDataBlock,
        }

        subtype = SUBTYPE_CLASSES.get(block_subtype)

        if subtype is None:
            raise DataBlockUnknownException(f"Unknown data block subtype: {block_subtype}")
        
        return subtype.from_payload(payload=payload)


# Debug Message
class DebugMessageDataBlock(DataBlock):
    def __init__(self, mission_time: int, debug_msg: str):
        super().__init__(DataBlockSubtype.DEBUG_MESSAGE, mission_time)
        self.debug_msg = debug_msg

    def __len__(self) -> int:
        return ((len(self.debug_msg.encode("utf-8")) + 3) & ~0x3) + 4

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        mission_time = struct.unpack("<I", payload[0:4])[0]
        return DebugMessageDataBlock(mission_time, payload[4:].decode("utf-8"))

    def to_payload(self) -> bytes:
        b = self.debug_msg.encode("utf-8")
        b = b + (b"\x00" * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f'{self.__class__.__name__} -> time: {self.mission_time} ms, message: "{self.debug_msg}"'

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "message", self.debug_msg


class StartupMessageDataBlock(DataBlock):
    def __init__(self, mission_time: int, startup_msg):
        super().__init__(DataBlockSubtype.STARTUP_MESSAGE, mission_time)
        self.startup_msg = startup_msg

    def __len__(self) -> int:
        return ((len(self.startup_msg.encode("utf-8")) + 3) & ~0x3) + 4

    @classmethod
    def from_payload(cls, payload: bytes):
        mission_time = struct.unpack("<I", payload[0:4])[0]
        return StartupMessageDataBlock(mission_time, payload[4:].decode("utf-8"))

    def to_payload(self) -> bytes:
        b = self.startup_msg.encode("utf-8")
        b = b + (b"\x00" * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f'{self.__class__.__name__} -> time: {self.mission_time} ms, message: "{self.startup_msg}"'

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "message", self.startup_msg


# Software Status
class SensorStatus(IntEnum):
    SENSOR_STATUS_NONE = 0x0
    SENSOR_STATUS_INITIALIZING = 0x1
    SENSOR_STATUS_RUNNING = 0x2
    SENSOR_STATUS_SELF_TEST_FAILED = 0x3
    SENSOR_STATUS_FAILED = 0x4

    def __str__(self):
        match self:
            case SensorStatus.SENSOR_STATUS_NONE:
                return "none"
            case SensorStatus.SENSOR_STATUS_INITIALIZING:
                return "initializing"
            case SensorStatus.SENSOR_STATUS_RUNNING:
                return "running"
            case SensorStatus.SENSOR_STATUS_SELF_TEST_FAILED:
                return "self test failed"
            case SensorStatus.SENSOR_STATUS_FAILED:
                return "failed"
            case _:
                return "unknown"


class SDCardStatus(IntEnum):
    SD_CARD_STATUS_NOT_PRESENT = 0x0
    SD_CARD_STATUS_INITIALIZING = 0x1
    SD_CARD_STATUS_READY = 0x2
    SD_CARD_STATUS_FAILED = 0x3

    def __str__(self):
        match self:
            case SDCardStatus.SD_CARD_STATUS_NOT_PRESENT:
                return "card not present"
            case SDCardStatus.SD_CARD_STATUS_INITIALIZING:
                return "initializing"
            case SDCardStatus.SD_CARD_STATUS_READY:
                return "ready"
            case SDCardStatus.SD_CARD_STATUS_FAILED:
                return "failed"
            case _:
                return "unknown"


class DeploymentState(IntEnum):
    DEPLOYMENT_STATE_DNE = -1
    DEPLOYMENT_STATE_IDLE = 0x0
    DEPLOYMENT_STATE_ARMED = 0x1
    DEPLOYMENT_STATE_POWERED_ASCENT = 0x2
    DEPLOYMENT_STATE_COASTING_ASCENT = 0x3
    DEPLOYMENT_STATE_DROGUE_DEPLOY = 0x4
    DEPLOYMENT_STATE_DROGUE_DESCENT = 0x5
    DEPLOYMENT_STATE_MAIN_DEPLOY = 0x6
    DEPLOYMENT_STATE_MAIN_DESCENT = 0x7
    DEPLOYMENT_STATE_RECOVERY = 0x8

    def __str__(self):
        match self:
            case DeploymentState.DEPLOYMENT_STATE_IDLE:
                return "idle"
            case DeploymentState.DEPLOYMENT_STATE_ARMED:
                return "armed"
            case DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT:
                return "powered ascent"
            case DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT:
                return "coasting ascent"
            case DeploymentState.DEPLOYMENT_STATE_DROGUE_DEPLOY:
                return "drogue deployed"
            case DeploymentState.DEPLOYMENT_STATE_DROGUE_DESCENT:
                return "drogue descent"
            case DeploymentState.DEPLOYMENT_STATE_MAIN_DEPLOY:
                return "main deployed"
            case DeploymentState.DEPLOYMENT_STATE_MAIN_DESCENT:
                return "main descent"
            case DeploymentState.DEPLOYMENT_STATE_RECOVERY:
                return "recovery"
            case DeploymentState.DEPLOYMENT_STATE_DNE:
                return ""
            case _:
                return "unknown"


# TODO type hint some of this stuff lol. //// nou
class StatusDataBlock(DataBlock):
    """Encapsulates the status data."""

    def __init__(
        self,
        mission_time: int,
        kx134_state: SensorStatus,
        alt_state: SensorStatus,
        imu_state: SensorStatus,
        sd_state: SDCardStatus,
        deployment_state: DeploymentState,
        sd_blocks_recorded: int,
        sd_checkouts_missed: int,
    ):
        super().__init__(DataBlockSubtype.STATUS, mission_time)
        self.kx134_state: SensorStatus = kx134_state
        self.alt_state: SensorStatus = alt_state
        self.imu_state: SensorStatus = imu_state
        self.sd_state: SDCardStatus = sd_state
        self.deployment_state: DeploymentState = deployment_state
        self.sd_blocks_recorded: int = sd_blocks_recorded
        self.sd_checkouts_missed: int = sd_checkouts_missed

    def __len__(self) -> int:
        return 16

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<IIII", payload)

        try:
            kx134_state = SensorStatus((parts[1] >> 16) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 state: {(parts[1] >> 16) & 0x7}") from error

        try:
            alt_state = SensorStatus((parts[1] >> 19) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid altimeter state: {(parts[1] >> 19) & 0x7}") from error

        try:
            imu_state = SensorStatus((parts[1] >> 22) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid IMU state: {(parts[1] >> 22) & 0x7}") from error

        try:
            sd_state = SDCardStatus((parts[1] >> 25) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid SD card state: {(parts[1] >> 25) & 0x7}") from error

        try:
            deployment_state = DeploymentState((parts[1] >> 28) & 0xF)
        except ValueError as error:
            raise DataBlockException(f"Invalid deployment state: {(parts[1] >> 28) & 0xf}") from error

        return StatusDataBlock(
            parts[0], kx134_state, alt_state, imu_state, sd_state, deployment_state, parts[2], parts[3]
        )

    def to_payload(self) -> bytes:
        states = (
            ((self.kx134_state.value & 0x7) << 16)
            | ((self.alt_state.value & 0x7) << 19)
            | ((self.imu_state.value & 0x7) << 22)
            | ((self.sd_state.value & 0x7) << 25)
            | ((self.deployment_state.value & 0x7) << 28)
        )

        return struct.pack("<IIII", self.mission_time, states, self.sd_blocks_recorded, self.sd_checkouts_missed)

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, kx134 state: "
            f"{str(self.kx134_state)}, altimeter state: {str(self.alt_state)}, "
            f"IMU state: {str(self.imu_state)}, SD driver state: {str(self.sd_state)}, "
            f"deployment state: {str(self.deployment_state)}, blocks recorded: "
            f" {self.sd_blocks_recorded}, checkouts missed: {self.sd_checkouts_missed}"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "kx134_state", self.kx134_state
        yield "altimeter_state", self.alt_state
        yield "imu_state", self.imu_state
        yield "sd_driver_state", self.sd_state
        yield "deployment_state", self.deployment_state
        yield "blocks_recorded", self.sd_blocks_recorded
        yield "checkouts_missed", self.sd_checkouts_missed


# Altitude
class AltitudeDataBlock(DataBlock):
    """Contains the data pertaining to the altitude block."""

    def __init__(self, mission_time: int, pressure: int, temperature: int, altitude: int):
        super().__init__(DataBlockSubtype.ALTITUDE, mission_time)
        self.pressure: int = pressure
        self.temperature: int = temperature
        self.altitude: int = altitude

    def __len__(self) -> int:
        return 16

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<Iiii", payload)
        return AltitudeDataBlock(parts[0], parts[1], parts[2] / 1000, parts[3] / 1000)

    def to_payload(self) -> bytes:
        return struct.pack(
            "<Iiii", self.mission_time, int(self.pressure), int(self.temperature * 1000), int(self.altitude * 1000)
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, pressure: {self.pressure} Pa, "
            f"temperature: {self.temperature} C, altitude: {self.altitude} m"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "pressure", {"pascals": self.pressure, "psi": converter.pascals_to_psi(self.pressure)}
        yield "altitude", {"metres": self.altitude, "feet": converter.metres_to_feet(self.altitude)}
        yield "temperature", {
            "celsius": self.temperature,
            "fahrenheit": converter.celsius_to_fahrenheit(self.temperature),
        }


class AccelerationDataBlock(DataBlock):
    def __init__(self, mission_time: int, fsr: int, x: int, y: int, z: int):
        super().__init__(DataBlockSubtype.ACCELERATION, mission_time)
        self.mission_time: int = mission_time
        self.fsr: int = fsr
        self.x: int = x
        self.y: int = y
        self.z: int = z

    def __len__(self) -> int:
        return 12

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<IBBhhh", payload)
        fsr = parts[1]
        x = parts[3] * (fsr / (2**15))
        y = parts[4] * (fsr / (2**15))
        z = parts[5] * (fsr / (2**15))
        return AccelerationDataBlock(parts[0], fsr, x, y, z)

    def to_payload(self) -> bytes:
        x = round(self.x * ((2**15) / self.fsr))
        y = round(self.y * ((2**15) / self.fsr))
        z = round(self.z * ((2**15) / self.fsr))
        return struct.pack("<IBBhhh", self.mission_time, self.fsr, 0, x, y, z)

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time}, fsr: {self.fsr}, "
            f"x: {self.x} g, y: {self.y} g, z: {self.z} g"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "fsr", self.fsr
        yield "x", self.x
        yield "y", self.y
        yield "z", self.y


#
#   Angular Velocity
#
class AngularVelocityDataBlock(DataBlock):
    def __init__(self, mission_time: int, fsr: int, x: int, y: int, z: int):
        super().__init__(DataBlockSubtype.ANGULAR_VELOCITY, mission_time)
        self.fsr: int = fsr
        self.x: int = x
        self.y: int = y
        self.z: int = z

    def __len__(self) -> int:
        return 12

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<IHhhh", payload)
        fsr = parts[1]
        x = parts[2] * (fsr / (2**15))
        y = parts[3] * (fsr / (2**15))
        z = parts[4] * (fsr / (2**15))
        return AngularVelocityDataBlock(parts[0], fsr, x, y, z)

    def to_payload(self) -> bytes:
        x = round(self.x * ((2**15) / self.fsr))
        y = round(self.y * ((2**15) / self.fsr))
        z = round(self.z * ((2**15) / self.fsr))
        return struct.pack("<IHhhh", self.mission_time, self.fsr, x, y, z)

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time}, fsr: {self.fsr}, "
            f"x: {self.x} g, y: {self.y} g, z: {self.z} g"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "fsr", self.fsr
        yield "x", self.x
        yield "y", self.y
        yield "z", self.z


# GNSS Location
class GNSSLocationFixType(IntEnum):
    UNKNOWN = 0
    NOT_AVAILABLE = 1
    FIX_2D = 2
    FIX_3D = 3


class GNSSLocationBlock(DataBlock):
    """The data for GNSS location."""

    def __init__(
        self,
        mission_time: int,
        latitude: int,
        longitude: int,
        utc_time: int,
        altitude: int,
        speed: int,
        course: int,
        pdop: int,
        hdop: int,
        vdop: int,
        sats: int,
        fix_type: GNSSLocationFixType,
    ):
        super().__init__(DataBlockSubtype.GNSS, mission_time)
        self.latitude: int = latitude
        self.longitude: int = longitude
        self.utc_time: int = utc_time
        self.altitude: int = altitude
        self.speed: int = speed
        self.course: int = course
        self.pdop: int = pdop
        self.hdop: int = hdop
        self.vdop: int = vdop
        self.sats: int = sats
        self.fix_type = fix_type

    def __len__(self) -> int:
        return 32

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<IiiIihhHHHBB", payload)

        try:
            fix_type = GNSSLocationFixType(parts[11] & 0x3)
        except ValueError as error:
            raise DataBlockException(f"Invalid GNSS fix type: {parts[11] >> 6:04x}") from error

        return GNSSLocationBlock(
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4] / 1000,
            parts[5] / 100,
            parts[6] / 100,
            parts[7] / 100,
            parts[8] / 100,
            parts[9] / 100,
            parts[10],
            fix_type,
        )

    def to_payload(self) -> bytes:
        return struct.pack(
            "<IiiIihhHHHBB",
            self.mission_time,
            self.latitude,
            self.longitude,
            self.utc_time,
            int(self.altitude * 1000),
            int(self.speed * 100),
            int(self.course * 100),
            int(self.pdop * 100),
            int(self.hdop * 100),
            int(self.vdop * 100),
            self.sats,
            self.fix_type & 0x3,
        )

    @staticmethod
    def coord_to_str(coord, ew=False):
        direction = coord >= 0
        coord = abs(coord)
        degrees = coord // 600000
        coord -= degrees * 600000
        minutes = coord // 10000
        coord -= minutes * 10000
        seconds = (coord * 6) / 1000

        if ew:
            direction_char = "E" if direction else "W"
        else:
            direction_char = "N" if direction else "W"

        return f"{degrees}°{minutes}'{seconds:.3f}{direction_char}"

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time}, position: "
            f"{(self.latitude / 600000)} {(self.longitude / 600000)}, utc time: "
            f"{self.utc_time}, altitude: {self.altitude} m, speed: {self.speed} knots, "
            f"course: {self.course} degs, pdop: {self.pdop}, hdop: {self.hdop}, vdop: "
            f"{self.vdop}, sats in use: {self.sats}, type: {self.fix_type.name}"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "position", {"latitude": (self.latitude / 600000), "longitude": (self.longitude / 600000)}
        yield "utc_time", self.utc_time
        yield "altitude", self.altitude
        yield "speed", self.speed
        yield "course", self.course
        yield "pdop", self.pdop
        yield "hdop", self.hdop
        yield "vdop", self.vdop
        yield "sats_in_use", self.sats
        yield "fix_type", self.fix_type


class GNSSSatType(IntEnum):
    """The types of GNSS satellites."""

    GPS = 0
    GLONASS = 1


class GNSSSatInfo:
    """The information packet for the GNSS satellite info"""

    GPS_SV_OFFSET: int = 0
    GLONASS_SV_OFFSET: int = 65

    def __init__(self, sat_type: GNSSSatType, elevation: int, snr: int, identifier: int, azimuth: int):
        self.sat_type: GNSSSatType = sat_type
        self.elevation: int = elevation
        self.snr: int = snr
        self.identifier: int = identifier
        self.azimuth: int = azimuth

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<BBH", payload)
        identifier = parts[2] & 0x1F

        try:
            sat_type = GNSSSatType((parts[2] >> 15) & 0x1)
        except ValueError:
            raise DataBlockException(f"Invalid GNSS sat type: {(parts[2] >> 15) & 0x1}")

        if sat_type == GNSSSatType.GPS:
            identifier = identifier + GNSSSatInfo.GPS_SV_OFFSET
        elif sat_type == GNSSSatType.GLONASS:
            identifier = identifier + GNSSSatInfo.GLONASS_SV_OFFSET

        azimuth = (parts[2] << 5) & 0x1FF

        return GNSSSatInfo(sat_type, parts[0], parts[1], identifier, azimuth)

    def to_payload(self) -> bytes:
        if self.sat_type == GNSSSatType.GPS:
            id_adjusted = self.identifier - GNSSSatInfo.GPS_SV_OFFSET
        else:
            id_adjusted = self.identifier - GNSSSatInfo.GLONASS_SV_OFFSET

        id_and_azimuth = (id_adjusted & 0x1F) | ((self.azimuth & 0x1FF) << 5) | (self.sat_type << 15)

        return struct.pack("<BBH", self.elevation, self.snr, id_and_azimuth)

    def __str__(self):
        return (
            f"{self.sat_type.name} sat -> elevation: "
            f"{self.elevation} degs, SNR: {self.snr} dB-Hz, id: {self.identifier}, "
            f"azimuth: {self.azimuth} degs"
        )

    def __iter__(self):
        yield "sat_type", self.sat_type.name
        yield "elevation", self.elevation
        yield "snr", self.snr
        yield "id", self.identifier
        yield "azimuth", self.azimuth


class GNSSMetadataBlock(DataBlock):
    def __init__(
        self,
        mission_time: int,
        gps_sats_in_use: list[int],
        glonass_sats_in_use: list[int],
        sats_in_view: list[GNSSSatInfo],
    ):
        super().__init__(DataBlockSubtype.GNSS_META, mission_time)
        self.gps_sats_in_use: list[int] = gps_sats_in_use
        self.glonass_sats_in_use: list[int] = glonass_sats_in_use
        self.sats_in_view: list[GNSSSatInfo] = sats_in_view

    def __len__(self) -> int:
        return 12 + (len(self.sats_in_view) * 4)

    @classmethod
    def from_payload(cls, payload: bytes):
        # There are 3 uint32_t variables, one for time, gps sats in use, and glonass sats in use
        # The remaining of the payload is an array for sats in view, each 4 bytes being a unique GNSSSatInfo struct
        # 12 bytes is 96 bits (3 x 32)
        offset = 12

        parts = struct.unpack("<III", payload[0:offset])
        payload_time = parts[0]
        gps_sats_in_use = list()
        glonass_sats_in_use = list()
        sats_in_view = list()

        # Check satellites in use bitfields
        for i in range(32):
            if parts[1] & (1 << i):
                gps_sats_in_use.append(i + GNSSSatInfo.GPS_SV_OFFSET)
            if parts[2] & (1 << i):
                glonass_sats_in_use.append(i + GNSSSatInfo.GLONASS_SV_OFFSET)

        # Check satellites in view array
        while offset < len(payload):
            sats_in_view.append(GNSSSatInfo.from_payload(payload[offset : offset + 4]))
            offset += 4

        return GNSSMetadataBlock(payload_time, gps_sats_in_use, glonass_sats_in_use, sats_in_view)

    def to_payload(self) -> bytes:
        gps_sats_in_use_bitfield = 0
        for n in self.gps_sats_in_use:
            gps_sats_in_use_bitfield |= 1 << (n - GNSSSatInfo.GPS_SV_OFFSET)

        glonass_sats_in_use_bitfield = 0
        for n in self.glonass_sats_in_use:
            glonass_sats_in_use_bitfield |= 1 << (n - GNSSSatInfo.GLONASS_SV_OFFSET)

        payload = struct.pack("<III", self.mission_time, gps_sats_in_use_bitfield, glonass_sats_in_use_bitfield)

        for sat in self.sats_in_view:
            payload = payload + sat.to_payload()

        return payload

    def __str__(self):
        s = (
            f"{self.__class__.__name__} -> time: {self.mission_time}, GPS sats in use: "
            f"{self.gps_sats_in_use}, GLONASS sats in use: {self.glonass_sats_in_use}\n"
            f"Sats in view:"
        )
        for sat in self.sats_in_view:
            s += f"\n\t{str(sat)} " if dict(sat)["snr"] != 0 else ""
        return s

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "gps_sats_in_use", self.gps_sats_in_use
        yield "glonass_sats_in_use", self.glonass_sats_in_use
        yield "sats_in_view", [dict(sat) for sat in self.sats_in_view if dict(sat)["snr"] != 0]


class KX134ODR(IntEnum):
    ODR_781 = 0
    ODR_1563 = 1
    ODR_3125 = 2
    ODR_6250 = 3
    ODR_12500 = 4
    ODR_25000 = 5
    ODR_50000 = 6
    ODR_100000 = 7
    ODR_200000 = 8
    ODR_400000 = 9
    ODR_800000 = 10
    ODR_1600000 = 11
    ODR_3200000 = 12
    ODR_6400000 = 13
    ODR_12800000 = 14
    ODR_25600000 = 15

    @property
    def samples_per_sec(self) -> float:
        return 25600.0 / (2 ** (15 - self))

    def __str__(self):
        return f"{self.samples_per_sec} Hz"


class KX134Range(IntEnum):
    ACCEL_8G = 0
    ACCEL_16G = 1
    ACCEL_32G = 2
    ACCEL_64G = 3

    @property
    def acceleration(self):
        match self:
            case KX134Range.ACCEL_8G:
                return 8
            case KX134Range.ACCEL_16G:
                return 16
            case KX134Range.ACCEL_32G:
                return 32
            case KX134Range.ACCEL_64G:
                return 64
            case _:
                return 0

    def __str__(self):
        return f"±{self.acceleration} g"


class KX134LPFRolloff(IntEnum):
    ODR_OVER_9 = 0
    ODR_OVER_2 = 1

    def __str__(self):
        return "ODR / 9" if self == KX134LPFRolloff.ODR_OVER_9 else "ODR / 2"


class KX134Resolution(IntEnum):
    RES_8_BIT = 0
    RES_16_BIT = 1

    @property
    def bits(self):
        if self == KX134Resolution.RES_8_BIT:
            return 8
        elif self == KX134Resolution.RES_16_BIT:
            return 16
        return 0

    def __str__(self):
        return f"{self.bits} bits per sample"


class KX134AccelerometerDataBlock(DataBlock):
    def __init__(
        self,
        mission_time: int,
        odr: KX134ODR,
        accel_range: KX134Range,
        rolloff: KX134LPFRolloff,
        resolution: KX134Resolution,
        samples: list,
    ):
        super().__init__(DataBlockSubtype.KX134_1211_ACCEL, mission_time)
        self.odr: KX134ODR = odr
        self.accel_range: KX134Range = accel_range
        self.rolloff: KX134LPFRolloff = rolloff
        self.resolution: KX134Resolution = resolution
        self.samples: list = samples

        self.sample_period = 1 / self.odr.samples_per_sec

    def __len__(self) -> int:
        sample_bytes = len(self.samples) * int(self.resolution.bits / 8) * 3
        return (sample_bytes + 6 + 3) & ~0x3

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<IH", payload[0:6])

        try:
            odr = KX134ODR(parts[1] & 0xF)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 ODR: {parts[1] & 0xf}") from error

        try:
            accel_range = KX134Range((parts[1] >> 4) & 0x3)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 range: {(parts[1] >> 4) & 0x3}") from error

        try:
            rolloff = KX134LPFRolloff((parts[1] >> 6) & 0x1)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 rolloff: {(parts[1] >> 6) & 0x1}") from error

        try:
            resolution = KX134Resolution((parts[1] >> 6) & 0x1)
        except ValueError as error:
            raise DataBlockException(f"Invalid KX134 res: {(parts[1] >> 7) & 0x1}") from error

        padding = (parts[1] >> 14) & 0x3
        num_samples = (len(payload) - (6 + padding)) // ((resolution.bits // 8) * 3)

        samples = list()
        sensitivity = (2 ** (resolution.bits - 1)) // accel_range.acceleration
        for i in range(num_samples):
            if resolution == KX134Resolution.RES_8_BIT:
                samp_start = 6 + (i * 3)
                samp_parts = struct.unpack("<bbb", payload[samp_start : samp_start + 3])
            else:
                samp_start = 6 + (i * 6)
                samp_parts = struct.unpack("<hhh", payload[samp_start : samp_start + 6])

            x = samp_parts[0] / sensitivity
            y = samp_parts[1] / sensitivity
            z = samp_parts[2] / sensitivity

            # print(f"i: {i}, samp_start: {samp_start}, x: {x}, y: {y}, z: {z}, samp_parts: {samp_parts}")

            samples.append((x, y, z))

        return KX134AccelerometerDataBlock(parts[0], odr, accel_range, rolloff, resolution, samples)

    def to_payload(self) -> bytes:
        sample_bytes = len(self.samples) * int(self.resolution.bits // 8) * 3
        padding = len(self) - (sample_bytes + 6)

        settings = (
            (self.odr & 0xF)
            | ((self.accel_range & 0x3) << 4)
            | ((self.rolloff & 0x1) << 6)
            | ((self.resolution & 0x1) << 7)
            | ((padding & 0x3) << 14)
        )
        head = struct.pack("<IH", self.mission_time, settings)

        sensitivity = (2 ** (self.resolution.bits - 1)) // self.accel_range.acceleration
        for sample in self.samples:
            x = int(sample[0] * sensitivity)
            y = int(sample[1] * sensitivity)
            z = int(sample[2] * sensitivity)

            if self.resolution == KX134Resolution.RES_8_BIT:
                head = head + struct.pack("<bbb", x, y, z)
            else:
                head = head + struct.pack("<hhh", x, y, z)

        return head + (b"\x00" * padding)

    def gen_samples(self):
        count = len(self.samples)
        for i, samp in enumerate(self.samples):
            time = (self.mission_time * (1000 / 1024)) - ((count - i) * (self.sample_period * 1024))
            yield time, samp[0], samp[1], samp[2]

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time}, samples: {len(self.samples)}, "
            f"ODR: {self.odr}, range: {self.accel_range}, rolloff: {self.rolloff}, "
            f"resolution: {self.resolution}"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "samples", len(self.samples)
        yield "odr", self.odr
        yield "range", self.accel_range
        yield "rolloff", self.rolloff
        yield "resolution", self.resolution


class MPU9250MagSR(IntEnum):
    SR_8 = 0
    SR_100 = 1

    @property
    def samples_per_sec(self):
        return self.value

    def __str__(self):
        return f"{self.samples_per_sec} Hz"


class MPU9250AccelFSR(IntEnum):
    ACCEL_2G = 0
    ACCEL_4G = 1
    ACCEL_8G = 2
    ACCEL_16G = 3

    @property
    def acceleration(self):
        return self.value

    @property
    def sensitivity(self):
        return 32768 / self.value

    def __str__(self):
        return f"+/-{self.value} g"


class MPU9250GyroFSR(IntEnum):
    AV_250DPS = 0
    AV_500DPS = 1
    AV_1000DPS = 2
    AV_2000DPS = 3

    @property
    def angular_velocity(self):
        return self.value

    @property
    def sensitivity(self):
        return 32768 / self.value

    def __str__(self):
        return f"+/-{self.value} deg/s"


class MPU9250AccelBW(IntEnum):
    BW_5_HZ = 0
    BW_10_HZ = 1
    BW_21_HZ = 2
    BW_45_HZ = 3
    BW_99_HZ = 4
    BW_218_HZ = 5
    BW_420_HZ = 6

    @property
    def bandwidth(self):
        match self:
            case MPU9250AccelBW.BW_5_HZ:
                return 5.05
            case MPU9250AccelBW.BW_10_HZ:
                return 10.2
            case MPU9250AccelBW.BW_21_HZ:
                return 21.2
            case MPU9250AccelBW.BW_45_HZ:
                return 44.8
            case MPU9250AccelBW.BW_99_HZ:
                return 99
            case MPU9250AccelBW.BW_218_HZ:
                return 218.1
            case MPU9250AccelBW.BW_420_HZ:
                return 420
            case _:
                return 0

    def __str__(self):
        return f"{self.bandwidth} Hz"


class MPU9250GyroBW(IntEnum):
    BW_5_HZ = 0
    BW_10_HZ = 1
    BW_20_HZ = 2
    BW_41_HZ = 3
    BW_92_HZ = 4
    BW_184_HZ = 5
    BW_250_HZ = 6

    @property
    def bandwidth(self):
        match self:
            case MPU9250GyroBW.BW_5_HZ:
                return 5
            case MPU9250GyroBW.BW_10_HZ:
                return 10
            case MPU9250GyroBW.BW_20_HZ:
                return 20
            case MPU9250GyroBW.BW_41_HZ:
                return 41
            case MPU9250GyroBW.BW_92_HZ:
                return 92
            case MPU9250GyroBW.BW_184_HZ:
                return 184
            case MPU9250GyroBW.BW_250_HZ:
                return 250
            case _:
                return 0

    def __str__(self):
        return f"{self.bandwidth} Hz"


class MPU9250MagResolution(IntEnum):
    RES_14_BIT = 0
    RES_16_BIT = 1

    @property
    def bits(self):
        match self:
            case MPU9250MagResolution.RES_14_BIT:
                return 14
            case MPU9250MagResolution.RES_16_BIT:
                return 16
            case _:
                return 0

    @property
    def sensitivity(self):
        match self:
            case MPU9250MagResolution.RES_14_BIT:
                return 1 / 0.6
            case MPU9250MagResolution.RES_16_BIT:
                return 1 / 0.15
            case _:
                return 0

    def __str__(self):
        return f"{self.bits} bits per sample"


class MPU9250Sample:
    def __init__(
        self,
        accel_x: int,
        accel_y: int,
        accel_z: int,
        temperature: int,
        gyro_x: int,
        gyro_y: int,
        gyro_z: int,
        mag_x: int,
        mag_y: int,
        mag_z: int,
        mag_ovf: int,
        mag_res: MPU9250MagResolution,
    ):
        self.accel_x: int = accel_x
        self.accel_y: int = accel_y
        self.accel_z: int = accel_z
        self.temperature: int = temperature
        self.gyro_x: int = gyro_x
        self.gyro_y: int = gyro_y
        self.gyro_z: int = gyro_z
        self.mag_x: int = mag_x
        self.mag_y: int = mag_y
        self.mag_z: int = mag_z
        self.mag_ovf: int = mag_ovf
        self.mag_res: MPU9250MagResolution = mag_res

    @classmethod
    def from_bytes(cls, payload, accel_sense, gyro_sense):
        ag_parts = struct.unpack(">hhhhhhh", payload[0:14])
        mag_parts = struct.unpack("<hhhB", payload[14:21])

        accel_x = ag_parts[0] / accel_sense
        accel_y = ag_parts[1] / accel_sense
        accel_z = ag_parts[2] / accel_sense

        temperature = (ag_parts[3] / 321) + 21

        gyro_x = ag_parts[4] / gyro_sense
        gyro_y = ag_parts[5] / gyro_sense
        gyro_z = ag_parts[6] / gyro_sense

        mag_ovf = bool((mag_parts[3] >> 4) & 1)
        mag_res = MPU9250MagResolution((mag_parts[3] >> 3) & 1)

        mag_x = mag_parts[0] / mag_res.sensitivity
        mag_y = mag_parts[1] / mag_res.sensitivity
        mag_z = mag_parts[2] / mag_res.sensitivity

        return MPU9250Sample(
            accel_x, accel_y, accel_z, temperature, gyro_x, gyro_y, gyro_z, mag_x, mag_y, mag_z, mag_ovf, mag_res
        )

    def to_payload(self, accel_sense: float, gyro_sense: float) -> bytes:
        accel_x = int(self.accel_x * accel_sense)
        accel_y = int(self.accel_y * accel_sense)
        accel_z = int(self.accel_z * accel_sense)

        temperature = int((self.temperature - 21) * 321)

        gyro_x = int(self.gyro_x * gyro_sense)
        gyro_y = int(self.gyro_y * gyro_sense)
        gyro_z = int(self.gyro_z * gyro_sense)

        mag_x = int(self.mag_x * self.mag_res.sensitivity)
        mag_y = int(self.mag_y * self.mag_res.sensitivity)
        mag_z = int(self.mag_z * self.mag_res.sensitivity)
        mag_flags = (int(self.mag_ovf) << 4) | (self.mag_res.value << 3)

        ag_bytes = struct.pack(">hhhhhhh", accel_x, accel_y, accel_z, temperature, gyro_x, gyro_y, gyro_z)
        mag_bytes = struct.pack("<hhhB", mag_x, mag_y, mag_z, mag_flags)
        return ag_bytes + mag_bytes

    def __iter__(self):
        yield "accel_x", self.accel_x
        yield "accel_y", self.accel_y
        yield "accel_z", self.accel_z
        yield "temperature", self.temperature
        yield "gyro_x", self.gyro_x
        yield "gyro_y", self.gyro_y
        yield "gyro_z", self.gyro_z
        yield "mag_x", self.mag_x
        yield "mag_y", self.mag_y
        yield "mag_z", self.mag_z
        yield "mag_ovf", self.mag_ovf
        yield "mag_res", self.mag_res


class MPU9250IMUDataBlock(DataBlock):
    def __init__(
        self,
        mission_time: int,
        ag_sample_rate: int,
        mag_sample_rate: MPU9250MagSR,
        accel_fsr: MPU9250AccelFSR,
        gyro_fsr: MPU9250GyroFSR,
        accel_bw: MPU9250AccelBW,
        gyro_bw: MPU9250GyroBW,
        samples: list[MPU9250Sample],
    ):
        super().__init__(DataBlockSubtype.MPU9250_IMU, mission_time)
        self.ag_sample_rate: int = ag_sample_rate
        self.mag_sample_rate: MPU9250MagSR = mag_sample_rate
        self.accel_fsr: MPU9250AccelFSR = accel_fsr
        self.gyro_fsr: MPU9250GyroFSR = gyro_fsr
        self.accel_bw: MPU9250AccelBW = accel_bw
        self.gyro_bw: MPU9250GyroBW = gyro_bw
        self.samples = samples

        self.sample_period = 1 / self.ag_sample_rate

        self.sensor = avg_mpu9250_samples(self.samples)

    def __len__(self) -> int:
        sample_bytes = len(self.samples) * 21
        return (sample_bytes + 8 + 3) & ~0x3

    @classmethod
    def from_payload(cls, payload: bytes):
        parts = struct.unpack("<II", payload[0:8])

        ag_sample_rate = 1000 / ((parts[1] & 0xFF) + 1)

        try:
            mag_sample_rate = MPU9250MagSR((parts[1] >> 8) & 0x1)
        except ValueError as error:
            raise DataBlockException(
                f"Invalid MPU9250 magnetometer sample " f"rate: {(parts[1] >> 8) & 0x1}"
            ) from error

        try:
            accel_fsr = MPU9250AccelFSR((parts[1] >> 9) & 0x3)
        except ValueError as error:
            raise DataBlockException(
                f"Invalid MPU9250 accelerometer full scale " f"range: {(parts[1] >> 9) & 0x3}"
            ) from error

        try:
            gyro_fsr = MPU9250GyroFSR((parts[1] >> 11) & 0x3)
        except ValueError as error:
            raise DataBlockException(
                f"Invalid MPU9250 gyroscope full scale " f"range: {(parts[1] >> 11) & 0x3}"
            ) from error

        try:
            accel_bw = MPU9250AccelBW((parts[1] >> 13) & 0x7)
        except ValueError as error:
            raise DataBlockException(
                f"Invalid MPU9250 accelerometer bandwidth: " f"{(parts[1] >> 13) & 0x7}"
            ) from error

        try:
            gyro_bw = MPU9250GyroBW((parts[1] >> 16) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 gyroscope bandwidth: " f"{(parts[1] >> 16) & 0x7}") from error

        num_samples = (len(payload) - 8) // 21

        samples = list()
        for i in range(num_samples):
            sample_start = 8 + (i * 21)
            sample = MPU9250Sample.from_bytes(
                payload[sample_start : sample_start + 21], accel_fsr.sensitivity, gyro_fsr.sensitivity
            )
            samples.append(sample)

        return MPU9250IMUDataBlock(
            parts[0], ag_sample_rate, mag_sample_rate, accel_fsr, gyro_fsr, accel_bw, gyro_bw, samples
        )

    def to_payload(self) -> bytes:
        ag_sr_div = (1000 // self.ag_sample_rate) - 1
        info = (
            (int(ag_sr_div) & 0xFF)
            | ((self.mag_sample_rate.value & 0x1) << 8)
            | ((self.accel_fsr.value & 0x3) << 9)
            | ((self.gyro_fsr.value & 0x3) << 11)
            | ((self.accel_bw.value & 0x7) << 13)
            | ((self.gyro_bw.value & 0x7) << 16)
        )

        content_length = 8 + (21 * len(self.samples))
        total_length = (content_length + 3) & ~0x3
        padding = total_length - content_length

        payload = struct.pack("<II", self.mission_time, info)

        for sample in self.samples:
            this_sample = sample.to_payload(self.accel_fsr.sensitivity, self.gyro_fsr.sensitivity)
            payload += this_sample

        return payload + (b"\x00" * padding)

    def gen_samples(self):
        count = len(self.samples)
        for i, samp in enumerate(self.samples):
            time = (self.mission_time * (1000 / 1024)) - ((count - i) * self.sample_period)
            yield time, samp

    def __str__(self):
        return (
            f"{self.__class__.__name__} -> time: {self.mission_time} ms, accel: ({self.sensor.accel_x},{self.sensor.accel_y},{self.sensor.accel_z}), temp: {self.sensor.temperature}, "
            f"gyro: ({self.sensor.gyro_x},{self.sensor.gyro_y},{self.sensor.gyro_z}), "
            f"samples: {len(self.samples)}, "
            f"sample rate: {self.ag_sample_rate} Hz, accel FSR: {self.accel_fsr}, "
            f"gyro fsr: {self.gyro_fsr}"
        )

    def __iter__(self):
        yield "mission_time", self.mission_time
        yield "accel_x", self.sensor.accel_x
        yield "accel_y", self.sensor.accel_y
        yield "accel_z", self.sensor.accel_z
        yield "temperature", self.sensor.temperature
        yield "gyro_x", self.sensor.gyro_x
        yield "gyro_y", self.sensor.gyro_y
        yield "gyro_z", self.sensor.gyro_z
        yield "mag_x", self.sensor.mag_x
        yield "mag_y", self.sensor.mag_y
        yield "mag_z", self.sensor.mag_z
        yield "mag_ovf", self.sensor.mag_ovf
        yield "mag_res", self.sensor.mag_res
        yield "samples", len(self.samples)
        yield "sensor_sample_rate", self.ag_sample_rate
        yield "accel_fsr", self.accel_fsr
        yield "gyro_fsr", self.gyro_fsr


def avg_mpu9250_samples(data_samples: list[MPU9250Sample]) -> MPU9250Sample:
    """
    Parses a list of samples from a mpu9250 packet and returns the average values for accel, temp, gyro and magnetometer
    """
    mag_ovf = data_samples[0].mag_ovf
    mag_res = data_samples[0].mag_res

    avg = dict.fromkeys(dict(data_samples[0]).keys(), 0)

    for sample in data_samples:
        data = dict(sample)
        for key in data.keys():
            avg[key] += data[key] / len(data_samples)

    return MPU9250Sample(
        avg["accel_x"],
        avg["accel_y"],
        avg["accel_z"],
        avg["temperature"],
        avg["gyro_x"],
        avg["gyro_y"],
        avg["gyro_z"],
        avg["mag_x"],
        avg["mag_y"],
        avg["mag_z"],
        mag_ovf,
        mag_res,
    )
