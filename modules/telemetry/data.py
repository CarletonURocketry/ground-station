# Contains the status data object class
__author__ = "Matteo Golin"

import json

# Imports
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias
from modules.telemetry.parsing_utils import ParsedBlock

# Aliases
OutputFormat: TypeAlias = dict[str, dict[str, dict[str, dict[str, str]]]]

logger = logging.getLogger(__name__)


@dataclass
class TelemetryDataPacket:
    """A generic block object to store information for telemetry data
    All stored values must be updated at once!"""

    mission_time: list[int] = field(default_factory=list[int])
    stored_values: dict[str, list[int]] = field(default_factory=dict)

    def update(self, data: dict[str, int], buffer_size: int) -> None:
        """Updates the stored values with the given data
        Args:
            data (dict[str, int]) : Dictionary of data to update containing mission_time and stored_values squashed
            buffer_size (int) : Size of the telemetry buffer"""

        # Ensure you are not half updating the packet
        # As this can cause the arrays to become out of sync and meaningless.
        if dict(self).keys() != data.keys():
            logger.error("Block must be updated using a full set of values at the same time!")
            logger.debug(f"Tried updating {dict(self).keys()} using {data.keys()}!")
            return

        # Updates stored values with new values
        for key in data.keys():
            if key == "mission_time":
                self.mission_time.append(data["mission_time"])
            else:
                self.stored_values[key].append(data[key])

        # Ensure buffer sizes are kept
        # Note: This uses a while loop incase buffer size shrinks drastically
        while len(self.mission_time) > buffer_size:
            self.mission_time.pop(0)
            for key in self.stored_values.keys():
                self.stored_values[key].pop(0)

    def clear(self) -> None:
        """Clears all stored values"""
        self.mission_time = []
        self.stored_values = {key: [] for key in self.stored_values.keys()}

    def __str__(self):
        """Returns a string representation of the TelemetryDataPacket"""
        return f"{self.__class__.__name__} -> time: {self.mission_time} ms, {self.stored_values}"

    def __iter__(self):
        """Returns an interator containing all the stored values"""
        yield "mission_time", self.mission_time
        for key in self.stored_values.keys():
            yield key, self.stored_values[key]


class TelemetryData:
    """Contains the output specification for the telemetry data block"""

    def __init__(self, telemetry_buffer_size: int = 20):
        """
        Initializes the telemetry data object.
        Args:
             telemetry_buffer_size: The size of the data buffer.
        """

        logger.debug(f"Initializing TelemetryData[{telemetry_buffer_size}]")
        self.buffer_size: int = telemetry_buffer_size
        self.decoder: list[dict[int, dict[str, str]]] = [{} for _ in range(5)]

        self.last_mission_time: int = -1
        self.output_blocks: dict[str, TelemetryDataPacket] = {}
        self.update_buffer: dict[str, dict[str, float | int | str | None]] = {}

        # Read packet definition file
        filepath = os.path.join(Path(__file__).parents[0], "telemetry_packet.json")
        with open(filepath, "r") as file:
            output_format: OutputFormat = dict(json.load(file))

        # Generate telemetry data packet from output specification
        for key in output_format.keys():
            telemetry_keys: list[str] = list(output_format[key].keys())
            self.output_blocks[key] = TelemetryDataPacket(stored_values={key: [] for key in telemetry_keys})
            self.update_buffer[key] = {key: None for key in telemetry_keys}

        # Generate extremely efficient access decoder matrix
        #                                        = {INPUT: OUTPUT}     "dataPacketBlockName.storedValueVariable"
        # decoder[packet_version][block_subtype] = {"gps_sats_in_use": "sats_in_use.gps_sats_in_use"}
        for data_packet in output_format.keys():
            for stored_value in output_format[data_packet].keys():
                for version in output_format[data_packet][stored_value].keys():
                    for block in output_format[data_packet][stored_value][version].keys():
                        input_key: str = output_format[data_packet][stored_value][version][block]
                        output_key: str = f"{data_packet}.{stored_value}"

                        existing: dict[str, str] = self.decoder[int(version)].get(int(block), {})
                        existing[input_key] = output_key
                        self.decoder[int(version)][int(block)] = existing

    def update_telemetry(self, packet_version: int, blocks: list[ParsedBlock]) -> None:
        """Updates telemetry object from given parsed blocks
        Args:
            packet_version (int): The packet encoding version
            blocks (list[ParsedBlock]): A list of parsed block objects"""

        # Extract block data
        for block in blocks:
            block_num: int = block.block_header.message_subtype
            block_decode: dict[str, str] = self.decoder[packet_version][block_num]
            data: dict[str, int | dict[str, int]] = block.block_contents

            logger.debug(f"{block}")

            try:
                # Update last mission time
                if data["mission_time"] > self.last_mission_time:  # type: ignore
                    self.last_mission_time = data["mission_time"]  # type: ignore

                # Grab input values and put them in update buffer (to fill output packets)
                for key in block_decode.keys():
                    destinationBlock: str = block_decode[key].split(".")[0]
                    destinationValue: str = block_decode[key].split(".")[1]
                    # Extract data and associated mission time to buffer
                    self.update_buffer[destinationBlock]["mission_time"] = data["mission_time"]  # type: ignore
                    if "." in key:
                        datakey: str = key.split(".")[0]
                        datasubkey: str = key.split(".")[1]
                        self.update_buffer[destinationBlock][destinationValue] = data[datakey][  # type: ignore
                            datasubkey
                        ]
                    else:
                        self.update_buffer[destinationBlock][destinationValue] = data[key]  # type: ignore

                # Check if we filled any packet during this block extraction
                for key in self.update_buffer.keys():
                    if None not in self.update_buffer[key].values():
                        # Let's update packet
                        self.output_blocks[key].update(self.update_buffer[key], self.buffer_size)  # type: ignore
                        # Clear packets buffer
                        for subkey in self.update_buffer[key].keys():
                            self.update_buffer[key][subkey] = None
            except KeyError as e:
                logger.error(f"Telemetry parsed block data issue. Missing key {e}")

    def update_buffer_size(self, new_buffer_size: int = 20) -> None:
        """Allows updating the telemetry buffer size without recreating object"""
        self.buffer_size = new_buffer_size

    def clear(self) -> None:
        """Clears the telemetry output data packet entirely"""
        self.last_mission_time = -1
        # Clear buffer
        for dest_block in self.update_buffer.keys():
            for dest_value in self.update_buffer[dest_block].keys():
                self.update_buffer[dest_block][dest_value] = None
        # Clear packet blocks
        for block in self.output_blocks.values():
            block.clear()

    def __iter__(self):
        """Returns an iterator containing all the packets"""
        yield "last_mission_time", self.last_mission_time
        for key in self.output_blocks.keys():
            yield key, dict(self.output_blocks[key])
