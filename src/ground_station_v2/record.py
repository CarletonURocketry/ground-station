from pathlib import Path
from src.ground_station_v2.radio.packets.spec import ParsedTransmission
import os
from time import time

# saves data in the "recordings" dir
# recording dir has child dirs for each mission, the default name is the timestamp but it should have the ability to be renamed
# each child dir has a raw and a parsed version of the incoming radio data
# the raw data should be in hex format
# the parsed data should be a collection of csvs, one for each sensor type
# the recoding class is a singleton, which means it can only be instantiated once
# it's methods are async, which means we don't need threads or processes, just one asyncio task


# TODO: Make all methods async? I don't think its needed?
class Record:
    _instance = None

    raw_file = None

    # Commented as the parsed data will be in multiple csv files
    # parsed_file = None

    mission_name = time()

    recording = False

    # singleton pattern
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # create the recordings directory if it doesn't exist
            Path("recordings").mkdir(exist_ok=True)
        return cls._instance
    

    def init_mission(self, recordings_path: str, mission_name: str | None = None):
        if mission_name:
            self.mission_name = mission_name

        os.makedirs(f"{recordings_path}/{self.mission_name}", exist_ok=True)

        self.raw_file = open(recordings_path + f"/{self.mission_name}/raw", "w")
        # TODO: Make 'parsed' a folder of csvs
        # self.parsed_file = open(recordings_path + f"/{self.mission_name}/parsed", "w")

    def close_mission(self):
        # if not self.raw_file or not self.parsed_file:
        #     raise FileExistsError("Mission not initialized")

        if not self.raw_file:
            raise FileExistsError("Mission not initialized")

        self.raw_file.close()
        # self.parsed_file.close()
    

    def write(self, raw_packet: str, parsed_packet: ParsedTransmission | None):
        # if not self.raw_file or not self.parsed_file:
        #     raise FileExistsError("Mission not initialized")

        if not self.raw_file:
            raise FileExistsError("Mission not initialized")
        
        self.raw_file.write(raw_packet + "\n")
        # TODO: Write data of parsed packets
        # self.parsed_file.write(str(parsed_packet) + "\n")
        

    def start(self):
        self.recording = True

    def stop(self):
        self.recording = False
