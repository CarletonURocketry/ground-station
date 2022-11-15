# Replays sensor packets from the mission file
# Outputs data blocks to the UI
#
# Authors:
# Thomas Selwyn (Devil)


from time import time, sleep
import csv
from multiprocessing import Process, Queue

from pathlib import Path
from modules.telemetry.data_block import DataBlock, DataBlockSubtype


class TelemetryReplay(Process):
    def __init__(self, replay_payloads: Queue, replay_input: Queue, replay_path: Path):
        super().__init__()

        self.replay_payloads = replay_payloads
        self.replay_path = replay_path
        self.replay_start = int(time())


        self.mission_start = -1


        with open(self.replay_path, newline='') as csvfile:
            self.run(csvfile)

    def run(self, file):
        index = 0

        mission_reader = csv.reader(file)

        while True:
            for row in mission_reader:
                if index == 0:
                    print(f"FILE TYPE {row[0]}. MISSION EPOCH {row[1]}")
                else:

                    block_type, block_subtype, block_payload = int(row[0]), int(row[1]), bytes.fromhex(row[2])

                    if int(block_type) == 2:
                        block_data = DataBlock.parse(DataBlockSubtype(block_subtype), block_payload)

                        replay_data = (block_type, block_subtype, block_data)
                        self.replay_payloads.put(replay_data)
                        sleep(0.02)

                index = index + 1


