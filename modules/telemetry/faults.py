# Telemetry Fault Checker
# Incoming information comes from telemetry in data block format
# Returns json of all faults detected in current data block
#
# Authors:
# Thomas Selwyn (Devil)
import logging

from modules.telemetry.data_block import DataBlock, AltitudeDataBlock, AccelerationDataBlock, AngularVelocityDataBlock, \
    GNSSLocationBlock, \
    GNSSMetadataBlock, MPU9250IMUDataBlock, KX134AccelerometerDataBlock
from modules.telemetry.block import DataBlockSubtype, BlockException, BlockUnknownException
from modules.misc.thresholds import FaultThresholds

LOW: int = 0
HYSTERESIS: int = 1
HIGH: int = 2


def run_fault_check(data_block: DataBlock, thresholds: FaultThresholds, telem_history: dict) -> dict:
    try:
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

        return {"set": False if len(fault_list) == 0 else True, "faults": fault_list}

    except KeyError as e:
        logging.error(f"Fault Thresholds encountered config error, unable to read {str(e)}")


def run_general_check(data_block: DataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    if data_block.mission_time < 0:
        fault_list += ["invalid_time"]

    return fault_list


def run_altitude_check(altitude_block: AltitudeDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Pressure
    if altitude_block.pressure < thresholds.rocket["pressure"][LOW]:
        fault_list += ["pressure_low"]
    if altitude_block.pressure < thresholds.rocket["pressure"][HIGH]:
        fault_list += ["pressure_high"]

    # Altitude
    if altitude_block.altitude < thresholds.rocket["altitude"][LOW]:
        fault_list += ["altitude_below_ground"]
    if altitude_block.altitude > thresholds.rocket["altitude"][HIGH]:
        fault_list += ["altitude_above_expected"]

    # Temperature
    # My god, we landed the rocket on the sun!
    if altitude_block.temperature > 5500:
        fault_list += ["rocket_on_sun"]

    if altitude_block.temperature < thresholds.rocket["temperature"][LOW]:
        fault_list += ["temp_low"]
    if altitude_block.temperature > thresholds.rocket["temperature"][HIGH]:
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

    # Altitude
    if gnss_block.altitude < thresholds.rocket["altitude"][LOW]:
        fault_list += ["altitude_below_ground"]
    if gnss_block.altitude > thresholds.rocket["altitude"][HIGH]:
        fault_list += ["altitude_above_expected"]
    # Why are we in space, cuz we're CU IN SPACE!
    if gnss_block.altitude > 100000:
        fault_list += ["rocket_in_space"]

    # Speed
    if gnss_block.speed < thresholds.rocket["speed"][LOW]:
        fault_list += ["bad_speed"]
    if gnss_block.speed > thresholds.rocket["speed"][HIGH]:
        fault_list += ["f1_rocket"]

    # Satellites
    if gnss_block.sats < thresholds.gnss["min_sats_in_use"]:
        fault_list += ["not_enough_sats"]
    if thresholds.gnss["verify_fix_type"] and gnss_block.fix_type != gnss_block.fix_type.FIX_3D:
        fault_list += ["bad_fix"]

    return fault_list


def run_gnss_meta_check(gnss_meta_block: GNSSMetadataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Just in case we aren't using satellites for some reason...
    if len(gnss_meta_block.gps_sats_in_use + gnss_meta_block.glonass_sats_in_use) == 0:
        fault_list += ["no_sats_in_use"]

    # I guess all sats fell out of the sky, and we are in some post apocalyptic time
    if len(gnss_meta_block.sats_in_view) == 0:
        fault_list += ["no_sats_in_view"]
    elif len(gnss_meta_block.sats_in_view) < thresholds.gnss_meta["min_sats_in_view"]:
        fault_list += ["low_sats_in_view"]

    return fault_list


def run_mpu9250_check(mpu_block: MPU9250IMUDataBlock, thresholds: FaultThresholds) -> [str]:
    fault_list = []

    # Mag overflow
    if thresholds.mpu9250_imu["mag_ovf"] and mpu_block.samples[0].mag_ovf:
        fault_list += ["mag_overflow"]

    return fault_list
