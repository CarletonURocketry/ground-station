# Telemetry Fault Checker
# Incoming information comes from telemetry in data block format
# Returns json of all faults detected in current data block
#
# Authors:
# Thomas Selwyn (Devil)
from modules.telemetry.data_block import DataBlock
from modules.telemetry.block import DataBlockSubtype, BlockException, BlockUnknownException


def run_fault_check(data_block: DataBlock):
    block_fault = {"set": False, "faults": []}

    # TODO: Add way more logic
    if data_block.subtype == DataBlockSubtype.MPU9250_IMU:
        block_fault["set"] = True
        block_fault["faults"] = ["mag_overflow"]

    # block_fault = {"set": True, "faults": ["temp_cold"]}
    return block_fault
