import struct
from abc import ABC, abstractmethod
from enum import Enum, IntEnum, auto


class DataBlockException(Exception):
    pass


class DataBlockUnknownException(DataBlockException):
    pass


class DataBlockSubtype(IntEnum):
    DEBUG_MESSAGE = 0x00
    STATUS = 0x01
    STARTUP = 0x02
    ALTITUDE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS = 0x06
    GNSS_META = 0x07
    POWER = 0x08
    TEMPERATURE = 0x09
    MPU9250_IMU = 0x0a
    KX134_1211_ACCEL = 0x0b


class DataBlock(ABC):
    @property
    @abstractmethod
    def length(self):
        """ Length of block """

    @property
    @abstractmethod
    def subtype(self):
        """ Subtype of block """

    @abstractmethod
    def to_payload(self):
        """ Marshal block to a bytes object """

    @staticmethod
    @abstractmethod
    def type_desc():
        """ String description of block type """

    @classmethod
    @abstractmethod
    def _parse(cls, payload):
        """ Unmarshal block from a bytes object (not meant to be called directly) """

    @classmethod
    def from_payload(cls, block_subtype, payload):
        """ Unmarshal a bytes object to appropriate block class """
        # 0x00
        if block_subtype == DataBlockSubtype.DEBUG_MESSAGE:
            return DebugMessageDataBlock._parse(payload)
        # 0x01
        if block_subtype == DataBlockSubtype.STATUS:
            return StatusDataBlock._parse(payload)

        if block_subtype == DataBlockSubtype.ALTITUDE:
            return AltitudeDataBlock._parse(payload)
        if block_subtype == DataBlockSubtype.ACCELERATION:
            return AccelerationDataBlock._parse(payload)
        if block_subtype == DataBlockSubtype.GNSS:
            return GNSSLocationBlock._parse(payload)
        if block_subtype == DataBlockSubtype.GNSS_META:
            return GNSSMetadataBlock._parse(payload)
        if block_subtype == DataBlockSubtype.MPU9250_IMU:
            return MPU9250IMUDataBlock._parse(payload)
        if block_subtype == DataBlockSubtype.KX134_1211_ACCEL:
            return KX134AccelerometerDataBlock._parse(payload)
        if block_subtype == DataBlockSubtype.ANGULAR_VELOCITY:
            return AngularVelocityDataBlock._parse(payload)

        raise DataBlockUnknownException(f"Unknown data block subtype: {block_subtype}")


#
#   Debug Message
#
class DebugMessageDataBlock(DataBlock):
    def __init__(self, mission_time, msg):
        self.mission_time = mission_time
        self.msg = msg

    @property
    def length(self):
        return ((len(self.msg.encode('utf-8')) + 3) & ~0x3) + 4

    @property
    def subtype(self):
        return DataBlockSubtype.DEBUG_MESSAGE

    @staticmethod
    def type_desc():
        return "Debug Message"

    @classmethod
    def _parse(cls, payload):
        mission_time = struct.unpack("<I", payload[0:4])[0]
        return DebugMessageDataBlock(mission_time, payload[4:].decode('utf-8'))

    def to_payload(self):
        b = self.msg.encode('utf-8')
        b = b + (b'\x00' * (((len(b) + 3) & ~0x3) - len(b)))
        return struct.pack("<I", self.mission_time) + b

    def __str__(self):
        return f"{self.type_desc()} -> mission_time: {self.mission_time}, message: \"{self.msg}\""


#
#   Software Status
#

class SensorStatus(IntEnum):
    SENSOR_STATUS_NONE = 0x0
    SENSOR_STATUS_INITIALIZING = 0x1
    SENSOR_STATUS_RUNNING = 0x2
    SENSOR_STATUS_SELF_TEST_FAILED = 0x3
    SENSOR_STATUS_FAILED = 0x4

    def __str__(self):
        if self == SensorStatus.SENSOR_STATUS_NONE:
            return "none"
        elif self == SensorStatus.SENSOR_STATUS_INITIALIZING:
            return "initializing"
        elif self == SensorStatus.SENSOR_STATUS_RUNNING:
            return "running"
        elif self == SensorStatus.SENSOR_STATUS_SELF_TEST_FAILED:
            return "self test failed"
        elif self == SensorStatus.SENSOR_STATUS_FAILED:
            return "failed"
        else:
            return "unknown"


class SDCardStatus(IntEnum):
    SD_CARD_STATUS_NOT_PRESENT = 0x0
    SD_CARD_STATUS_INITIALIZING = 0x1
    SD_CARD_STATUS_READY = 0x2
    SD_CARD_STATUS_FAILED = 0x3

    def __str__(self):
        if self == SDCardStatus.SD_CARD_STATUS_NOT_PRESENT:
            return "card not present"
        elif self == SDCardStatus.SD_CARD_STATUS_INITIALIZING:
            return "initializing"
        elif self == SDCardStatus.SD_CARD_STATUS_READY:
            return "ready"
        elif self == SDCardStatus.SD_CARD_STATUS_FAILED:
            return "failed"
        else:
            return "unknown"


class DeploymentState(IntEnum):
    DEPLOYMENT_STATE_IDLE = 0x0,
    DEPLOYMENT_STATE_ARMED = 0x1,
    DEPLOYMENT_STATE_POWERED_ASCENT = 0x2,
    DEPLOYMENT_STATE_COASTING_ASCENT = 0x3,
    DEPLOYMENT_STATE_DEPLOYING = 0x4,
    DEPLOYMENT_STATE_DESCENT = 0x5,
    DEPLOYMENT_STATE_RECOVERY = 0x6

    def __str__(self):
        if self == DeploymentState.DEPLOYMENT_STATE_IDLE:
            return "idle"
        elif self == DeploymentState.DEPLOYMENT_STATE_ARMED:
            return "armed"
        elif self == DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT:
            return "powered ascent"
        elif self == DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT:
            return "coasting ascent"
        elif self == DeploymentState.DEPLOYMENT_STATE_DEPLOYING:
            return "deploying"
        elif self == DeploymentState.DEPLOYMENT_STATE_DESCENT:
            return "descent"
        elif self == DeploymentState.DEPLOYMENT_STATE_RECOVERY:
            return "recovery"
        else:
            return "unknown"


class StatusDataBlock(DataBlock):
    def __init__(self, mission_time, kx134_state, alt_state, imu_state, sd_state,
                 deployment_state, sd_blocks_recorded, sd_checkouts_missed):
        self.mission_time = mission_time
        self.kx134_state = kx134_state
        self.alt_state = alt_state
        self.imu_state = imu_state
        self.sd_state = sd_state
        self.deployment_state = deployment_state
        self.sd_blocks_recorded = sd_blocks_recorded
        self.sd_checkouts_missed = sd_checkouts_missed

    @property
    def length(self):
        return 16

    @property
    def subtype(self):
        return DataBlockSubtype.STATUS

    @staticmethod
    def type_desc():
        return "Status"

    @classmethod
    def _parse(cls, payload):
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
            deployment_state = DeploymentState((parts[1] >> 28) & 0xf)
        except ValueError as error:
            raise DataBlockException(f"Invalid deployment state: {(parts[1] >> 28) & 0xf}") from error

        return StatusDataBlock(parts[0], kx134_state, alt_state, imu_state, sd_state,
                               deployment_state, parts[2], parts[3])

    def to_payload(self):
        states = (((self.kx134_state.value & 0x7) << 16) |
                  ((self.alt_state.value & 0x7) << 19) |
                  ((self.imu_state.value & 0x7) << 22) |
                  ((self.sd_state.value & 0x7) << 25) |
                  ((self.deployment_state.value & 0x7) << 28))

        return struct.pack("<IIII", self.mission_time, states, self.sd_blocks_recorded,
                           self.sd_checkouts_missed)

    def __str__(self):
        return (f"{self.type_desc()} -> mission_time: {self.mission_time}, kx_134 state: "
                f"{str(self.kx134_state)}, altimeter state: {str(self.alt_state)}, "
                f"IMU state: {str(self.imu_state)}, SD driver state: {str(self.sd_state)}, "
                f"deployment state: {str(self.deployment_state)}, blocks recorded: "
                f" {self.sd_blocks_recorded}, checkouts missed: {self.sd_checkouts_missed}")


#
#   Altitude
#
class AltitudeDataBlock(DataBlock):
    def __init__(self, mission_time, pressure, temperature, altitude):
        self.mission_time = mission_time
        self.pressure = pressure
        self.temperature = temperature
        self.altitude = altitude

    @property
    def length(self):
        return 16

    @property
    def subtype(self):
        return DataBlockSubtype.ALTITUDE

    @staticmethod
    def type_desc():
        return "Altitude"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<Iiii", payload)
        return AltitudeDataBlock(parts[0], parts[1], parts[2] / 1000, parts[3] / 1000)

    def to_payload(self):
        return struct.pack("<Iiii", self.mission_time, int(self.pressure),
                           int(self.temperature * 1000), int(self.altitude * 1000))

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, pressure: {self.pressure} Pa, "
                f"temperature: {self.temperature} C, altitude: {self.altitude} m")


#
#   Acceleration
#
class AccelerationDataBlock(DataBlock):
    def __init__(self, mission_time, fsr, x, y, z):
        self.mission_time = mission_time
        self.fsr = fsr
        self.x = x
        self.y = y
        self.z = z

    @property
    def length(self):
        return 12

    @property
    def subtype(self):
        return DataBlockSubtype.ALTITUDE

    @staticmethod
    def type_desc():
        return "Acceleration"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<IBBhhh", payload)
        fsr = parts[1]
        x = parts[3] * (fsr / (2 ** 15))
        y = parts[4] * (fsr / (2 ** 15))
        z = parts[5] * (fsr / (2 ** 15))
        return AccelerationDataBlock(parts[0], fsr, x, y, z)

    def to_payload(self):
        x = round(self.x * ((2 ** 15) / self.fsr))
        y = round(self.y * ((2 ** 15) / self.fsr))
        z = round(self.z * ((2 ** 15) / self.fsr))
        return struct.pack("<IBBhhh", self.mission_time, self.fsr, 0, x, y, z)

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, fsr: {self.fsr}, "
                f"x: {self.x} g, y: {self.y} g, z: {self.z} g")


#
#   Angular Velocity
#
class AngularVelocityDataBlock(DataBlock):
    def __init__(self, mission_time, fsr, x, y, z):
        self.mission_time = mission_time
        self.fsr = fsr
        self.x = x
        self.y = y
        self.z = z

    @property
    def length(self):
        return 12

    @property
    def subtype(self):
        return DataBlockSubtype.ANGULAR_VELOCITY

    @staticmethod
    def type_desc():
        return "Angular Velocity"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<IHhhh", payload)
        fsr = parts[1]
        x = parts[2] * (fsr / (2 ** 15))
        y = parts[3] * (fsr / (2 ** 15))
        z = parts[4] * (fsr / (2 ** 15))
        return AngularVelocityDataBlock(parts[0], fsr, x, y, z)

    def to_payload(self):
        x = round(self.x * ((2 ** 15) / self.fsr))
        y = round(self.y * ((2 ** 15) / self.fsr))
        z = round(self.z * ((2 ** 15) / self.fsr))
        return struct.pack("<IHhhh", self.mission_time, self.fsr, x, y, z)

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, fsr: {self.fsr}, "
                f"x: {self.x} g, y: {self.y} g, z: {self.z} g")


#
#   GNSS Location
#
class GNSSLocationFixType(IntEnum):
    UNKNOWN = 0x0
    NOT_AVAILABLE = 0x1
    FIX_2D = 0x2
    FIX_3D = 0x3


class GNSSLocationBlock(DataBlock):
    def __init__(self, mission_time, latitude, longitude, utc_time, altitude, speed, course, pdop,
                 hdop, vdop, sats, fix_type):
        self.mission_time = mission_time
        self.latitude = latitude
        self.longitude = longitude
        self.utc_time = utc_time
        self.altitude = altitude
        self.speed = speed
        self.course = course
        self.pdop = pdop
        self.hdop = hdop
        self.vdop = vdop
        self.sats = sats
        self.fix_type = fix_type

    @property
    def length(self):
        return 32

    @property
    def subtype(self):
        return DataBlockSubtype.GNSS

    @staticmethod
    def type_desc():
        return "GNSS Location"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<IiiIihhHHHBB", payload)

        try:
            fix_type = GNSSLocationFixType(parts[11] & 0x3)
        except ValueError as error:
            raise DataBlockException(f"Invalid GNSS fix type: {parts[11] >> 6:04x}") from error

        return GNSSLocationBlock(parts[0], parts[1], parts[2], parts[3], parts[4] / 1000,
                                 parts[5] / 100, parts[6] / 100, parts[7] / 100, parts[8] / 100,
                                 parts[9] / 100, parts[10], fix_type)

    def to_payload(self):
        return struct.pack("<IiiIihhHHHBB", self.mission_time, self.latitude, self.longitude,
                           self.utc_time, int(self.altitude * 1000), int(self.speed * 100),
                           int(self.course * 100), int(self.pdop * 100), int(self.hdop * 100),
                           int(self.vdop * 100), self.sats, self.fix_type & 0x3)

    @staticmethod
    def coord_to_str(coord, ew=False):
        direction = coord >= 0;
        coord = abs(coord)
        degrees = coord // 600000
        coord -= degrees * 600000
        minutes = coord // 10000
        coord -= minutes * 10000
        seconds = (coord * 6) / 1000

        direction_char = '?'
        if ew:
            direction_char = "E" if direction else "W"
        else:
            direction_char = "N" if direction else "W"

        return f"{degrees}°{minutes}'{seconds:.3f}{direction_char}"

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, position: "
                f"{GNSSLocationBlock.coord_to_str(self.latitude)} "
                f"{GNSSLocationBlock.coord_to_str(self.longitude, ew=True)}, utc time: "
                f"{self.utc_time}, altitude: {self.altitude} m, speed: {self.speed} knots, "
                f"course: {self.course}°, pdop: {self.pdop}, hdop: {self.hdop}, vdop: "
                f"{self.vdop}, sats in use: {self.sats}, type: {self.fix_type.name}")


#
#   GNSS Metadata
#
class GNSSSatType(IntEnum):
    GPS = 0
    GLONASS = 1


class GNSSSatInfo:
    GPS_SV_OFFSET = 0
    GLONASS_SV_OFFSET = 65

    def __init__(self, sat_type, elevation, snr, identifier, azimuth):
        self.sat_type = sat_type
        self.elevation = elevation
        self.snr = snr
        self.identifier = identifier
        self.azimuth = azimuth

    @classmethod
    def from_bytes(cls, data):
        parts = struct.unpack("<BBH", data)
        identifier = parts[2] & 0x1f

        try:
            sat_type = GNSSSatType((parts[2] >> 15) & 0x1)
        except ValueError:
            raise DataBlockException(f"Invalid GNSS sat type: {(parts[2] >> 15) & 0x1}")

        if sat_type == GNSSSatType.GPS:
            identifier = identifier + GNSSSatInfo.GPS_SV_OFFSET
        elif sat_type == GNSSSatType.GLONASS:
            identifier = identifier + GNSSSatInfo.GLONASS_SV_OFFSET

        azimuth = (parts[2] << 5) & 0x1ff

        return GNSSSatInfo(sat_type, parts[0], parts[1], identifier, azimuth)

    def to_bytes(self):
        if self.sat_type == GNSSSatType.GPS:
            id_adjusted = self.identifier - GNSSSatInfo.GPS_SV_OFFSET
        elif self.sat_type == GNSSSatType.GLONASS:
            id_adjusted = self.identifier - GNSSSatInfo.GLONASS_SV_OFFSET

        id_and_azimuth = ((id_adjusted & 0x1f) | ((self.azimuth & 0x1ff) << 5) |
                          (self.sat_type << 15))

        return struct.pack("<BBH", self.elevation, self.snr, id_and_azimuth)

    def __str__(self):
        return (f"{'GPS' if self.sat_type == GNSSSatType.GPS else 'GLONASS'} sat -> elevation: "
                f"{self.elevation}°, SNR: {self.snr} dB-Hz, id: {self.identifier}, azimuth: "
                f"{self.azimuth}°")


class GNSSMetadataBlock(DataBlock):
    def __init__(self, mission_time, gps_sats_in_use, glonass_sats_in_use, sats_in_view):
        self.mission_time = mission_time
        self.gps_sats_in_use = gps_sats_in_use
        self.glonass_sats_in_use = glonass_sats_in_use
        self.sats_in_view = sats_in_view

    @property
    def length(self):
        return 12 + (len(self.sats_in_view) * 4)

    @property
    def subtype(self):
        return DataBlockSubtype.GNSS_META

    @staticmethod
    def type_desc():
        return "GNSS Metadata"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<III", payload[0:12])

        gps_sats_in_use = set()
        for i in range(32):
            if (parts[1] & (1 << i)):
                gps_sats_in_use.add(i + GNSSSatInfo.GPS_SV_OFFSET)

        glonass_sats_in_use = set()
        for i in range(32):
            if (parts[1] & (1 << i)):
                glonass_sats_in_use.add(i + GNSSSatInfo.GLONASS_SV_OFFSET)

        sats_in_view = list()
        offset = 12
        while offset < len(payload):
            sats_in_view.append(GNSSSatInfo.from_bytes(payload[offset:offset + 4]))
            offset += 4

        return GNSSMetadataBlock(parts[0], gps_sats_in_use, glonass_sats_in_use, sats_in_view)

    def to_payload(self):
        gps_sats_in_use_bitfield = 0
        for n in self.gps_sats_in_use:
            gps_sats_in_use_bitfield |= (1 << (n - GNSSSatInfo.GPS_SV_OFFSET))

        glonass_sats_in_use_bitfield = 0
        for n in self.glonass_sats_in_use:
            glonass_sats_in_use_bitfield |= (1 << (n - GNSSSatInfo.GLONASS_SV_OFFSET))

        payload = struct.pack("<III", self.mission_time, gps_sats_in_use_bitfield,
                              glonass_sats_in_use_bitfield)

        for sat in self.sats_in_view:
            payload = payload + sat.to_bytes()

        return payload

    def __str__(self):
        s = (f"{self.type_desc()} -> time: {self.mission_time}, GPS sats in use: "
             f"{self.gps_sats_in_use}, GLONASS sats in use: {self.glonass_sats_in_use}\nSats in "
             f"view:")
        for sat in self.sats_in_view:
            s += f"\n\t{sat}"
        return s


#
#   KX134-1211 Acceleromter Data
#

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
    def samples_per_sec(self):
        return 25600.0 / (2 ** (15 - self.value))

    def __str__(self):
        return f"{self.samples_per_sec} Hz"


class KX134Range(IntEnum):
    ACCEL_8G = 0,
    ACCEL_16G = 1,
    ACCEL_32G = 2,
    ACCEL_64G = 3

    @property
    def acceleration(self):
        if self == KX134Range.ACCEL_8G:
            return 8
        elif self == KX134Range.ACCEL_16G:
            return 16
        elif self == KX134Range.ACCEL_32G:
            return 32
        elif self == KX134Range.ACCEL_64G:
            return 64
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
    TYPE_DESC = "KX134 Accelerometer Data"

    def __init__(self, mission_time, odr, accel_range, rolloff, resolution, samples):
        self.mission_time = mission_time
        self.odr = odr
        self.accel_range = accel_range
        self.rolloff = rolloff
        self.resolution = resolution
        self.samples = samples

        self.sample_period = 1 / self.odr.samples_per_sec

    @property
    def length(self):
        sample_bytes = len(self.samples) * int(self.resolution.bits / 8) * 3
        return (sample_bytes + 6 + 3) & ~0x3

    @property
    def subtype(self):
        return DataBlockSubtype.KX123_1211_ACCEL

    @staticmethod
    def type_desc():
        return "KX134 Accelerometer Data"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<IH", payload[0:6])

        try:
            odr = KX134ODR(parts[1] & 0xf)
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
                samp_parts = struct.unpack("<bbb", payload[samp_start:samp_start + 3])
            else:
                samp_start = 6 + (i * 6)
                samp_parts = struct.unpack("<hhh", payload[samp_start:samp_start + 6])

            x = samp_parts[0] / sensitivity
            y = samp_parts[1] / sensitivity
            z = samp_parts[2] / sensitivity

            # print(f"i: {i}, samp_start: {samp_start}, x: {x}, y: {y}, z: {z}, samp_parts: {samp_parts}")

            samples.append((x, y, z))

        return KX134AccelerometerDataBlock(parts[0], odr, accel_range, rolloff, resolution, samples)

    def to_payload(self):
        sample_bytes = len(self.samples) * int(self.resolution.bits // 8) * 3
        padding = self.length - (sample_bytes + 6)

        settings = ((self.odr & 0xf) | ((self.accel_range & 0x3) << 4) |
                    ((self.rolloff & 0x1) << 6) | ((self.resolution & 0x1) << 7) |
                    ((padding & 0x3) << 14))
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

        return head + (b'\x00' * padding)

    def gen_samples(self):
        count = len(self.samples)
        for i, samp in enumerate(self.samples):
            time = (self.mission_time * (1000 / 1024)) - ((count - i) * (self.sample_period * 1024))
            yield time, samp[0], samp[1], samp[2]

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, samples: {len(self.samples)}, "
                f"ODR: {self.odr}, range: {self.accel_range}, rolloff: {self.rolloff}, "
                f"resolution: {self.resolution}")


#
#   MPU9250 IMU Data
#

class MPU9250MagSR(IntEnum):
    SR_8 = 0
    SR_100 = 1

    @property
    def samples_per_sec(self):
        if self == MPU9250MagSR.SR_8:
            return 8
        elif self == MPU9250MagSR.SR_100:
            return 100
        else:
            return 0

    def __str__(self):
        return f"{self.samples_per_sec} Hz"


class MPU9250AccelFSR(IntEnum):
    ACCEL_2G = 0,
    ACCEL_4G = 1,
    ACCEL_8G = 2,
    ACCEL_16G = 3

    @property
    def acceleration(self):
        if self == MPU9250AccelFSR.ACCEL_2G:
            return 2
        elif self == MPU9250AccelFSR.ACCEL_4G:
            return 4
        elif self == MPU9250AccelFSR.ACCEL_8G:
            return 8
        elif self == MPU9250AccelFSR.ACCEL_16G:
            return 16
        return 0

    @property
    def sensitivity(self):
        return 32768 / self.acceleration

    def __str__(self):
        return f"±{self.acceleration} g"


class MPU9250GyroFSR(IntEnum):
    AV_250DPS = 0,
    AV_500DPS = 1,
    AV_1000DPS = 2,
    AV_2000DPS = 3

    @property
    def angular_velocity(self):
        if self == MPU9250GyroFSR.AV_250DPS:
            return 250
        elif self == MPU9250GyroFSR.AV_500DPS:
            return 500
        elif self == MPU9250GyroFSR.AV_1000DPS:
            return 1000
        elif self == MPU9250GyroFSR.AV_2000DPS:
            return 2000
        return 0

    @property
    def sensitivity(self):
        return 32768 / self.angular_velocity

    def __str__(self):
        return f"±{self.angular_velocity} °/s"


class MPU9250AccelBW(IntEnum):
    BW_5_HZ = 0,
    BW_10_HZ = 1,
    BW_21_HZ = 2,
    BW_45_HZ = 3,
    BW_99_HZ = 4,
    BW_218_HZ = 5,
    BW_420_HZ = 6

    @property
    def bandwidth(self):
        if self == MPU9250AccelBW.BW_5_HZ:
            return 5.05
        elif self == MPU9250AccelBW.BW_10_HZ:
            return 10.2
        elif self == MPU9250AccelBW.BW_21_HZ:
            return 21.2
        elif self == MPU9250AccelBW.BW_45_HZ:
            return 44.8
        elif self == MPU9250AccelBW.BW_99_HZ:
            return 99
        elif self == MPU9250AccelBW.BW_218_HZ:
            return 218.1
        elif self == MPU9250AccelBW.BW_420_HZ:
            return 420
        return 0

    def __str__(self):
        return f"{self.bandwidth} Hz"


class MPU9250GyroBW(IntEnum):
    BW_5_HZ = 0,
    BW_10_HZ = 1,
    BW_20_HZ = 2,
    BW_41_HZ = 3,
    BW_92_HZ = 4,
    BW_184_HZ = 5,
    BW_250_HZ = 6

    @property
    def bandwidth(self):
        if self == MPU9250GyroBW.BW_5_HZ:
            return 5
        elif self == MPU9250GyroBW.BW_10_HZ:
            return 10
        elif self == MPU9250GyroBW.BW_20_HZ:
            return 20
        elif self == MPU9250GyroBW.BW_41_HZ:
            return 41
        elif self == MPU9250GyroBW.BW_92_HZ:
            return 92
        elif self == MPU9250GyroBW.BW_184_HZ:
            return 184
        elif self == MPU9250GyroBW.BW_250_HZ:
            return 250
        return 0

    def __str__(self):
        return f"{self.bandwidth} Hz"


class MPU9250MagResolution(IntEnum):
    RES_14_BIT = 0
    RES_16_BIT = 1

    @property
    def bits(self):
        if self == MPU9250MagResolution.RES_14_BIT:
            return 14
        elif self == MPU9250MagResolution.RES_16_BIT:
            return 16
        return 0

    @property
    def sensitivity(self):
        if self == MPU9250MagResolution.RES_14_BIT:
            return 1 / 0.6
        elif self == MPU9250MagResolution.RES_16_BIT:
            return 1 / 0.15
        return 0

    def __str__(self):
        return f"{self.bits} bits per sample"


class MPU9250Sample:
    def __init__(self, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, mag_x,
                 mag_y, mag_z, mag_ovf, mag_res, temperature):
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.accel_z = accel_z
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z
        self.mag_x = mag_x
        self.mag_y = mag_y
        self.mag_z = mag_z
        self.mag_ovf = mag_ovf
        self.mag_res = mag_res
        self.temperature = temperature

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

        return MPU9250Sample(accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
                             mag_x, mag_y, mag_z, mag_ovf, mag_res, temperature)

    def to_bytes(self, accel_sense, gyro_sense):
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

        ag_bytes = struct.pack(">hhhhhhh", accel_x, accel_y, accel_z,
                               temperature, gyro_x, gyro_y, gyro_z)
        mag_bytes = struct.pack("<hhhB", mag_x, mag_y, mag_z, mag_flags)

        return ag_bytes + mag_bytes


class MPU9250IMUDataBlock(DataBlock):
    TYPE_DESC = "MPU9250 IMU Data"

    def __init__(self, mission_time, ag_sample_rate, mag_sample_rate, accel_fsr,
                 gyro_fsr, accel_bw, gyro_bw, samples):
        self.mission_time = mission_time
        self.ag_sample_rate = ag_sample_rate
        self.mag_sample_rate = mag_sample_rate
        self.accel_fsr = accel_fsr
        self.gyro_fsr = gyro_fsr
        self.accel_bw = accel_bw
        self.gyro_bw = gyro_bw
        self.samples = samples

        self.sample_period = 1 / self.ag_sample_rate

    @property
    def length(self):
        sample_bytes = len(self.samples) * 21
        return (sample_bytes + 8 + 3) & ~0x3

    @property
    def subtype(self):
        return DataBlockSubtype.KX123_1211_ACCEL

    @staticmethod
    def type_desc():
        return "MPU9250 IMU Data"

    @classmethod
    def _parse(cls, payload):
        parts = struct.unpack("<II", payload[0:8])

        ag_sample_rate = 1000 / ((parts[1] & 0xff) + 1)

        try:
            mag_sample_rate = MPU9250MagSR((parts[1] >> 8) & 0x1)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 magnetometer sample "
                                     f"rate: {(parts[1] >> 8) & 0x1}") from error

        try:
            accel_fsr = MPU9250AccelFSR((parts[1] >> 9) & 0x3)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 accelerometer full scale "
                                     f"range: {(parts[1] >> 9) & 0x3}") from error

        try:
            gyro_fsr = MPU9250GyroFSR((parts[1] >> 11) & 0x3)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 gyroscope full scale "
                                     f"range: {(parts[1] >> 11) & 0x3}") from error

        try:
            accel_bw = MPU9250AccelBW((parts[1] >> 13) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 accelerometer bandwidth: "
                                     f"{(parts[1] >> 13) & 0x7}") from error

        try:
            gyro_bw = MPU9250GyroBW((parts[1] >> 16) & 0x7)
        except ValueError as error:
            raise DataBlockException(f"Invalid MPU9250 gyroscope bandwidth: "
                                     f"{(parts[1] >> 16) & 0x7}") from error

        num_samples = (len(payload) - 8) // 21

        samples = list()
        for i in range(num_samples):
            sample_start = 8 + (i * 21)
            sample = MPU9250Sample.from_bytes(payload[sample_start:(sample_start + 21)],
                                              accel_fsr.sensitivity, gyro_fsr.sensitivity)
            samples.append(sample)

        return MPU9250IMUDataBlock(parts[0], ag_sample_rate, mag_sample_rate,
                                   accel_fsr, gyro_fsr, accel_bw, gyro_bw,
                                   samples)

    def to_payload(self):
        ag_sr_div = (1000 // self.ag_sample_rate) - 1
        info = ((ag_sr_div & 0xff) | ((self.mag_sample_rate.value & 0x1) << 8) |
                ((self.accel_fsr.value & 0x3) << 9) | ((self.gyro_fsr.value & 0x3) << 11) |
                ((self.accel_bw.value & 0x7) << 13) | ((self.gyro_bw.value & 0x7) << 16))

        content_length = 8 + (21 * len(self.samples))
        total_length = (content_length + 3) & ~0x3
        padding = total_length - content_length

        payload = struct.pack("<II", self.mission_time, info)

        for sample in self.samples:
            payload += sample.to_bytes(self.accel_fsr.sensitivity,
                                       self.gyro_fsr.sensitivity)

        return payload + (b'\x00' * padding)

    def gen_samples(self):
        count = len(self.samples)
        for i, samp in enumerate(self.samples):
            time = (self.mission_time * (1000 / 1024)) - ((count - i) * self.sample_period)
            yield time, samp

    def __str__(self):
        return (f"{self.type_desc()} -> time: {self.mission_time}, samples: {len(self.samples)}, "
                f"accel/gyro sample rate: {self.ag_sample_rate} Hz, accel FSR: {self.accel_fsr}, "
                f"gyro fsr: {self.gyro_fsr}")
