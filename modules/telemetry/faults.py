# Telemetry Fault Checker
# Incoming information comes from telemetry in data block format
# Returns json of all faults detected in current data block
#
# Authors:
# Thomas Selwyn (Devil)
from modules.telemetry.data_block import DataBlock, AltitudeDataBlock, MPU9250IMUDataBlock, GNSSLocationBlock, \
    GNSSMetadataBlock
from modules.telemetry.block import DataBlockSubtype, BlockException, BlockUnknownException


def run_fault_check(data_block: DataBlock) -> dict:
    fault_list = []

    match data_block.subtype:
        case DataBlockSubtype.ALTITUDE:
            fault_list = run_altitude_check(data_block)
        case DataBlockSubtype.MPU9250_IMU:
            fault_list = run_mpu9250_check(data_block)
        case DataBlockSubtype.GNSS:
            fault_list = run_gnss_check(data_block)
        case DataBlockSubtype.GNSS_META:
            fault_list = run_gnss_meta_check(data_block)

    return {"set": False if len(fault_list) == 0 else True, "faults": fault_list}


def run_altitude_check(altitude_block: AltitudeDataBlock) -> [str]:
    fault_list = []

    # My god, we landed the rocket on the sun!
    if altitude_block.temperature > 5500:
        fault_list += ["rocket_on_sun"]

    return fault_list


def run_mpu9250_check(mpu_block: MPU9250IMUDataBlock) -> [str]:
    fault_list = []

    # Mag overflow
    if mpu_block.samples[0].mag_ovf:
        fault_list += ["mag_overflow"]

    return fault_list


def run_gnss_check(gnss_block: GNSSLocationBlock) -> [str]:
    fault_list = []

    # Why are we in space
    if gnss_block.altitude > 100000:
        fault_list += ["rocket_in_space"]

    return fault_list


def run_gnss_meta_check(gnss_meta_block: GNSSMetadataBlock) -> [str]:
    fault_list = []

    # I guess all sats fell out of the sky, and we are in some post apocalyptic time
    if gnss_meta_block.sats_in_view == 0:
        fault_list += ["no_sats"]

    return fault_list
