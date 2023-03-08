# Replays sensor packets from the mission file
# Outputs data blocks to the UI
#
# Authors:
# Thomas Selwyn (Devil)

from time import time, sleep
import csv
from multiprocessing import Queue

from pathlib import Path
from modules.telemetry.block import BlockTypes
from modules.telemetry.data_block import DataBlock, DataBlockSubtype


class TelemetryReplay:
    def __init__(self, replay_payloads: Queue, replay_input: Queue, replay_path: Path):

        # Replay buffers (Input and output)
        self.replay_payloads = replay_payloads
        self.replay_input = replay_input

        # Misc replay
        self.replay_path = replay_path

        # Loop data
        self.last_loop_time = int(time() * 1000)
        self.total_time_offset = 0
        self.speed = 1

        with open(self.replay_path, 'r', newline='') as csvfile:
            self.run(csvfile)

    def run(self, csvfile):
        mission_reader = csv.reader(csvfile)

        while True:
            if self.speed > 0:
                self.read_next_line(mission_reader)

            if not self.replay_input.empty():
                self.parse_input_command(self.replay_input.get())

    def parse_input_command(self, data):
        split = data.split(" ")
        match split[0]:
            case "speed":
                self.speed = float(split[1])
                # Reset loop time so resuming playback doesn't skip the time it was paused
                self.last_loop_time = int(time() * 1000)

    def read_next_line(self, mission_reader):
        try:
            row = next(mission_reader)

            # we do not want misc mission details here
            if mission_reader.line_num == 1:
                return

            block_type, block_subtype, block_payload = int(row[0]), int(row[1]), str(row[2])

            if block_type == BlockTypes.DATA:
                block_data = DataBlock.parse(DataBlockSubtype(block_subtype), bytes.fromhex(block_payload))
                block_time = block_data.mission_time

                current_loop_time = int(time() * 1000)
                loop_time_offset = float(current_loop_time - self.last_loop_time) * self.speed

                self.total_time_offset += float(loop_time_offset)
                if self.total_time_offset < block_time:
                    next_block_wait = (block_time - self.total_time_offset) / self.speed
                    sleep(next_block_wait / 1000)

                self.last_loop_time = current_loop_time
                self.output_replay_data(block_type, block_subtype, block_payload)
        except StopIteration:
            self.speed = 0

    def output_replay_data(self, block_type, block_subtype, block_data):
        replay_data = (block_type, block_subtype, block_data)
        self.replay_payloads.put(replay_data)
