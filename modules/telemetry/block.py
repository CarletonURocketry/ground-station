# Generic block types and their subtypes
from enum import IntEnum


class BlockException(Exception):
    pass


class BlockUnknownException(BlockException):
    pass


class DeviceAddress(IntEnum):
    """ Lists the different device addresses packets can be sent from. """
    GROUND_STATION = 0x0
    ROCKET = 0x1
    MULTICAST = 0xF

    def __str__(self):
        match self:
            case DeviceAddress.GROUND_STATION:
                return "GROUND STATION"
            case DeviceAddress.ROCKET:
                return "ROCKET"
            case DeviceAddress.MULTICAST:
                return "MULTICAST"
            case _:
                return "UNKNOWN"


class RadioBlockType(IntEnum):
    """ Lists the different radio block classes. """

    CONTROL = 0x0
    COMMAND = 0x1
    DATA = 0x2
    RESERVED = 0xF


class SDBlockClassType(IntEnum):
    """ Lists the different SD Block classes. """

    LOGGING_METADATA = 0x0
    TELEMETRY_DATA = 0x1
    DIAGNOSTIC_DATA = 0x2
    TELEMETRY_CONTROL = 0x3
    TELEMETRY_COMMAND = 0x4
    RESERVED = 0x3F


class CommandBlockSubtype(IntEnum):
    """ Lists the subtypes of telemetry command blocks. """

    SIGNAL_REPORT = 0x00
    COMMAND_ACKNOWLEDGEMENT = 0x01
    COMMAND_NONCE_REQUEST = 0x02
    COMMAND_NONCE = 0x03
    BEACON = 0x04
    BEACON_RESPONSE = 0x05
    RESERVED = 0x3F


class ControlBlockSubtype(IntEnum):
    """ Lists the subtypes of telemetry control blocks. """

    RESET_ROCKET_AVIONICS = 0x00
    REQUEST_TELEMETRY_DATA = 0x01
    DEPLOY_PARACHUTE = 0x02
    TARE_SENSORS = 0x03
    RESERVED = 0x3F


class DataBlockSubtype(IntEnum):
    """ Lists the subtypes of telemetry data blocks. """

    DEBUG_MESSAGE = 0x00
    STATUS = 0x01
    STARTUP_MESSAGE = 0x02
    ALTITUDE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS = 0x06
    GNSS_META = 0x07
    POWER = 0x08
    TEMPERATURE = 0x09
    MPU9250_IMU = 0x0A
    KX134_1211_ACCEL = 0x0B
    RESERVED = 0x3F


class LoggingMetadataBlockSubtype(IntEnum):
    """ Lists the subtypes of logging meta blocks. """
    SPACER = 0x0


class DiagnosticDataBlockSubtype(IntEnum):
    """ Lists the subtypes of diagnostic blocks. """
    LOG_MESSAGE = 0x0
    OUTGOING_RADIO_PACKET = 0x1
    INCOMING_RADIO_PACKET = 0x2
