# Replays sensor packets from the mission file
# Outputs data blocks to the UI
#
# Authors:
# Thomas Selwyn (Devil)

from time import time, sleep
import csv
from multiprocessing import Queue

from pathlib import Path
from modules.telemetry.data_block import DataBlock, DataBlockSubtype


class TelemetryReplay:
    def __init__(self, replay_payloads: Queue, replay_input: Queue, replay_path: Path):

        self.replay_input = replay_input
        self.replay_payloads = replay_payloads
        self.replay_path = replay_path
        self.mission_start = -1

        self.last_loop_time = int(time() * 1000)
        self.replay_start = int(time() * 1000)
        self.total_offset = 0
        self.speed = 1

        with open(self.replay_path, 'r', newline='') as csvfile:
            self.run(csvfile)

    def run(self, csvfile):
        mission_reader = csv.reader(csvfile)

        while True:
            if self.speed > 0:
                self.readNextLine(mission_reader)

            if not self.replay_input.empty():
                self.parseInputCommand(self.replay_input.get())

    def parseInputCommand(self, data):
        split = data.split(" ")
        match split[0]:
            case "speed":
                self.speed = float(split[1])
                # Reset loop time so resuming playback doesn't skip the time it was paused
                self.last_loop_time = int(time() * 1000)

    def readNextLine(self, mission_reader):
        try:
            row = next(mission_reader)

            if mission_reader.line_num == 1:
                self.mission_start = row[1]
            else:
                block_type, block_subtype, block_payload = int(row[0]), int(row[1]), str(row[2])

                if int(block_type) == 2:
                    block_data = DataBlock.parse(DataBlockSubtype(block_subtype), bytes.fromhex(block_payload))
                    block_time = block_data.mission_time
                    #print(block_time, block_type, block_subtype, block_data)

                    current_loop_time = int(time() * 1000)
                    offset = float(current_loop_time - self.last_loop_time) * self.speed

                    self.last_loop_time = current_loop_time
                    self.total_offset += float(offset)

                    if self.total_offset < block_time:
                        next_block_wait = (block_time - self.total_offset) / self.speed
                        # print(f"Sleeping {int(next_block_wait)} milliseconds until next block is time")
                        sleep(next_block_wait / 1000)

                    self.outputReplay(block_type, block_subtype, block_payload)
        except StopIteration:
            self.speed = 0

    def outputReplay(self, block_type, block_subtype, block_data):
        replay_data = (block_type, block_subtype, block_data)
        self.replay_payloads.put(replay_data)
