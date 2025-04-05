# Contains the status data object class
__author__ = "Thomas Selwyn", "Matteo Golin", "Angus Jull"

# Imports
import logging
from typing import Any
from collections import defaultdict

from modules.telemetry.packet_spec.blocks import Block, TimedBlock

logger = logging.getLogger(__name__)


class TelemetryBuffer:
    """Contains the output specification for the telemetry data block"""

    def __init__(self, telemetry_buffer_size: int = 20):
        """
        Initializes the telemetry data object.
        Args:
             telemetry_buffer_size: The size of the data buffer.
        """

        logger.debug(f"Initializing TelemetryBuffer[{telemetry_buffer_size}]")
        self.buffer_size: int = telemetry_buffer_size
        self.last_mission_time: int = -1
        self.output_blocks: defaultdict[str, list[Block]] = defaultdict(list)

    def add(self, blocks: list[Block]) -> None:
        """Updates telemetry object from given parsed blocks
        Args:
            packet_version (int): The packet encoding version
            blocks (list[ParsedBlock]): A list of parsed block objects"""
        for block in blocks:
            if block is None:
                logger.warning("Received None block, skipping")
                continue
            if isinstance(block, TimedBlock):
                if block.measurement_time > self.last_mission_time:
                    self.last_mission_time = block.measurement_time

            block_buffer = self.output_blocks[type(block).__name__]
            block_buffer.append(block)
            # keep up to buffer_size blocks in the buffer, remove oldest blocks if buffer is full
            while len(block_buffer) > self.buffer_size:
                self.output_blocks[type(block).__name__].pop(0)

    def update_buffer_size(self, new_buffer_size: int = 20) -> None:
        """Allows updating the telemetry buffer size without recreating object"""
        self.buffer_size = new_buffer_size

    def clear(self) -> None:
        """Clears the telemetry output data packet entirely"""
        self.last_mission_time = -1
        self.output_blocks = defaultdict(list)

    def get(self) -> dict[str, Any]:
        """Returns the buffered telemetry data in the expected format"""
        output = default_telemetry_dict()
        for block_buffer in self.output_blocks.values():
            for block in block_buffer:
                # Don't actually remove blocks when they've been output,
                # re-transmit until they get pushed out of the buffer by new data
                block.output_formatted(output)

        return output


# fmt: off
def default_telemetry_dict() -> dict[str, Any]:
    """Creates an empty telemetry packet in the format expected by the frontend

    Returns:
        dict[str, Any]: An empty telemetry packet
    """
    return {
            "last_mission_time": -1,
            "altitude_sea_level": {
                "mission_time": [],
                "metres": [],
                "feet": []
            },
            "altitude_launch_level": {
                "mission_time": [],
                "metres": [],
                "feet": []
            },
            "linear_acceleration": {
                "mission_time": [],
                "x": [],
                "y": [],
                "z": [],
                "magnitude": [],
            },
            "angular_velocity": {
                "mission_time": [],
                "x": [],
                "y": [],
                "z": [],
                "magnitude": [],
            },
            "temperature": {
                "mission_time": [], 
                "celsius": []
            },
            "pressure": {
                "mission_time": [],
                "pascals": []
            },
            "humidity": {
                "mission_time": [],
                "percentage": []
            },
            "gnss": {
                "mission_time": [],
                 "latitude": [],
                 "longitude": []
            },
            "sats_in_use": {
                "mission_time": [], 
                "gps": [[], []], 
                "glonass": [[], []]
            },
            "voltage": {
                "mission_time": []
            }
        }


# fmt: on
