from enum import IntEnum

class DataBlockSubtype(IntEnum):
    """Lists the subtypes of data blocks that can be sent in Version 1 of the packet encoding format."""

    DEBUG_MESSAGE = 0x00
    ALTITUDE = 0x01
    TEMPERATURE = 0x02
    PRESSURE = 0x03
    ACCELERATION = 0x04
    ANGULAR_VELOCITY = 0x05
    GNSS_LOCATION = 0x06
    GNSS_METADATA = 0x07
    HUMIDITY = 0x08
    STATUS = 0x09
    RESERVED = 0xFF

    def __str__(self):
        match self:
            case DataBlockSubtype.DEBUG_MESSAGE:
                return "DEBUG MESSAGE"
            case DataBlockSubtype.ALTITUDE:
                return "ALTITUDE"
            case DataBlockSubtype.TEMPERATURE:
                return "TEMPERATURE"
            case DataBlockSubtype.PRESSURE:
                return "PRESSURE"
            case DataBlockSubtype.ACCELERATION:
                return "ACCELERATION"
            case DataBlockSubtype.ANGULAR_VELOCITY:
                return "ANGULAR VELOCITY"
            case DataBlockSubtype.GNSS_LOCATION:
                return "GNSS LOCATION"
            case DataBlockSubtype.GNSS_METADATA:
                return "GNSS METADATA"
            case DataBlockSubtype.HUMIDITY:
                return "HUMIDITY"
            case DataBlockSubtype.STATUS:
                return "STATUS"
            case _:
                return "RESERVED"
            
class SensorStatus(IntEnum):
    SENSOR_STATUS_NONE = 0x0
    SENSOR_STATUS_INITIALIZING = 0x1
    SENSOR_STATUS_RUNNING = 0x2
    SENSOR_STATUS_SELF_TEST_FAILED = 0x3
    SENSOR_STATUS_FAILED = 0x4

    def __str__(self):
        return {
            SensorStatus.SENSOR_STATUS_NONE: "none",
            SensorStatus.SENSOR_STATUS_INITIALIZING: "initializing",
            SensorStatus.SENSOR_STATUS_RUNNING: "running",
            SensorStatus.SENSOR_STATUS_SELF_TEST_FAILED: "self test failed",
            SensorStatus.SENSOR_STATUS_FAILED: "failed",
        }.get(self, "unknown")

class SDCardStatus(IntEnum):
    SD_CARD_STATUS_NOT_PRESENT = 0x0
    SD_CARD_STATUS_INITIALIZING = 0x1
    SD_CARD_STATUS_READY = 0x2
    SD_CARD_STATUS_FAILED = 0x3

    def __str__(self):
        return {
            SDCardStatus.SD_CARD_STATUS_NOT_PRESENT: "card not present",
            SDCardStatus.SD_CARD_STATUS_INITIALIZING: "initializing",
            SDCardStatus.SD_CARD_STATUS_READY: "ready",
            SDCardStatus.SD_CARD_STATUS_FAILED: "failed",
        }.get(self, "unknown")


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
        return {
            DeploymentState.DEPLOYMENT_STATE_IDLE: "idle",
            DeploymentState.DEPLOYMENT_STATE_ARMED: "armed",
            DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT: "powered ascent",
            DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT: "coasting ascent",
            DeploymentState.DEPLOYMENT_STATE_DROGUE_DEPLOY: "drogue deployed",
            DeploymentState.DEPLOYMENT_STATE_DROGUE_DESCENT: "drogue descent",
            DeploymentState.DEPLOYMENT_STATE_MAIN_DEPLOY: "main deployed",
            DeploymentState.DEPLOYMENT_STATE_MAIN_DESCENT: "main descent",
            DeploymentState.DEPLOYMENT_STATE_RECOVERY: "recovery",
            DeploymentState.DEPLOYMENT_STATE_DNE: "",
        }.get(self, "unknown")