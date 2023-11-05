# Telemetry Fault Checker
# Incoming information comes from telemetry in data block format
# Returns json of all faults detected in current data block
#
# Authors:
# Thomas Selwyn (Devil)
from modules.telemetry.data_block import DataBlock, AltitudeDataBlock, AccelerationDataBlock, AngularVelocityDataBlock, \
    GNSSLocationBlock, \
    GNSSMetadataBlock, MPU9250IMUDataBlock, KX134AccelerometerDataBlock
from modules.telemetry.block import DataBlockSubtype, BlockException, BlockUnknownException
from modules.misc.thresholds import FaultThresholds


def run_fault_check(data_block: DataBlock, thresholds: FaultThresholds) -> dict:
    fault_list = run_general_check(data_block, thresholds)

    match data_block.subtype:
        case DataBlockSubtype.ALTITUDE:
            fault_list += run_altitude_check(data_block, thresholds)
        case DataBlockSubtype.ACCELERATION:
            fault_list += run_acceleration_check(data_block, thresholds)
        case DataBlockSubtype.ANGULAR_VELOCITY:
            fault_list += run_angular_check(data_block, thresholds)
        case DataBlockSubtype.GNSS:
            fault_list += run_gnss_check(data_block, thresholds)
        case DataBlockSubtype.GNSS_META:
            fault_list += run_gnss_meta_check(data_block, thresholds)
        case DataBlockSubtype.MPU9250_IMU:
            fault_list += run_mpu9250_check(data_block, thresholds)

    #if len(fault_list) != 0:
    #    print(fault_list)
    return {"set": False if len(fault_list) == 0 else True, "faults": fault_list}


def run_general_check(data_block: DataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    if data_block.mission_time < 0:
        fault_list += ["invalid_time"]

    return fault_list


def run_altitude_check(altitude_block: AltitudeDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Pressure
    if altitude_block.pressure < thresholds.altitude["pressure"]["low"]:
        fault_list += ["pressure_low"]
    if altitude_block.pressure < thresholds.altitude["pressure"]["high"]:
        fault_list += ["pressure_high"]

    # Altitude
    if altitude_block.altitude < thresholds.altitude["altitude"]["low"]:
        fault_list += ["altitude_below_ground"]
    if altitude_block.altitude > thresholds.altitude["altitude"]["high"]:
        fault_list += ["altitude_above_expected"]

    # Temperature
    # My god, we landed the rocket on the sun!
    if altitude_block.temperature > 5500:
        fault_list += ["rocket_on_sun"]

    if altitude_block.temperature < thresholds.altitude["temperature"]["low"]:
        fault_list += ["temp_low"]
    if altitude_block.temperature > thresholds.altitude["temperature"]["high"]:
        fault_list += ["temp_high"]


    return fault_list


def run_acceleration_check(acceleration_block: AccelerationDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    if acceleration_block.fsr < 0:
        fault_list += ["invalid_fsr"]

    return fault_list


def run_angular_check(angular_block: AngularVelocityDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    if angular_block.fsr < 0:
        fault_list += ["invalid_fsr"]

    return fault_list


def run_gnss_check(gnss_block: GNSSLocationBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Why are we in space, cuz we're CU IN SPACE!
    if gnss_block.altitude > 100000:
        fault_list += ["rocket_in_space"]

    # Altitude
    if gnss_block.altitude < thresholds.altitude["altitude"]["low"]:
        fault_list += ["altitude_below_ground"]
    if gnss_block.altitude > thresholds.altitude["altitude"]["high"]:
        fault_list += ["altitude_above_expected"]

    return fault_list


def run_gnss_meta_check(gnss_meta_block: GNSSMetadataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # I guess all sats fell out of the sky, and we are in some post apocalyptic time
    if gnss_meta_block.sats_in_view == 0:
        fault_list += ["no_sats"]

    return fault_list


def run_mpu9250_check(mpu_block: MPU9250IMUDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Mag overflow
    if mpu_block.samples[0].mag_ovf:
        fault_list += ["mag_overflow"]

    return fault_list
