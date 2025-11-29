from pathlib import Path
from src.ground_station_v2.radio.packets.spec import ParsedTransmission
from time import time
from src.ground_station_v2.radio.packets.blocks import (
    AltitudeAboveSeaLevel,
    AltitudeAboveLaunchLevel,
    Temperature,
    Pressure,
    LinearAcceleration,
    AngularVelocity,
    Humidity,
    Coordinates,
    Voltage,
    MagneticField,
    FlightStatus,
    FlightError,
)
import csv


# saves data in the "recordings" dir
# recording dir has child dirs for each mission, the default name is the timestamp but it should have the ability to be renamed
# each child dir has a raw and a parsed version of the incoming radio data
# the raw data should be in hex format
# the parsed data should be a collection of csvs, one for each sensor type
# the recoding class is a singleton, which means it can only be instantiated once
# it's methods are async, which means we don't need threads or processes, just one asyncio task


from typing import TypedDict, Any
from io import TextIOWrapper

class FileConfig(TypedDict):
    filename: str
    file: TextIOWrapper | None
    # Dictwriter gives type errors in ide, but when fixed gives type error on run :/
    writer: Any | None
    field_names: list[str]
    
class Record:
    _instance = None

    raw_file = None
    mission_name = time()
    recording = False

    # Config for files
    parsed_files: dict[Any, FileConfig] = {
        AltitudeAboveSeaLevel: {"filename": "altitude_above_sea_level", "file": None, "writer": None, "field_names": ["measurement_time", "altitude"]},
        AltitudeAboveLaunchLevel: {"filename": "altitude_above_launch_level", "file": None, "writer": None, "field_names": ["measurement_time", "altitude"]},
        Temperature: {"filename": "temperature", "file": None, "writer": None, "field_names": ["measurement_time", "temperature"]},
        Pressure: {"filename": "pressure", "file": None, "writer": None, "field_names": ["measurement_time", "pressure"]},
        LinearAcceleration: {"filename": "linear_acceleration", "file": None, "writer": None, "field_names": ["measurement_time", "x_axis", "y_axis", "z_axis"]},
        AngularVelocity: {"filename": "angular_velocity", "file": None, "writer": None, "field_names": ["measurement_time", "x_axis", "y_axis", "z_axis"]},
        Humidity: {"filename": "humidity", "file": None, "writer": None, "field_names": ["measurement_time", "humidity"]},
        Coordinates: {"filename": "coordinates", "file": None, "writer": None, "field_names": ["measurement_time", "latitude", "longitude"]},
        Voltage: {"filename": "voltage", "file": None, "writer": None, "field_names": ["measurement_time", "voltage", "identifier"]},
        MagneticField: {"filename": "magnetic_field", "file": None, "writer": None, "field_names": ["measurement_time", "x_axis", "y_axis", "z_axis"]},
        FlightStatus: {"filename": "status_message", "file": None, "writer": None, "field_names": ["measurement_time", "flight_status"]},
        FlightError: {"filename": "error_message", "file": None, "writer": None, "field_names": ["measurement_time", "proc_id", "error_code"]},
    }

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

        Path(f"{recordings_path}/{self.mission_name}").mkdir(exist_ok=True)
        Path(f"{recordings_path}/{self.mission_name}/parsed").mkdir(exist_ok=True)

        self.raw_file = open(recordings_path + f"/{self.mission_name}/raw", "w")
        
        # When initializing files in init_mission:
        for value in self.parsed_files.values():
            filepath = f"{recordings_path}/{self.mission_name}/parsed/{value['filename']}.csv"

            file = open(filepath, "w", newline='')

            writer = csv.DictWriter(file, fieldnames=value['field_names'])
            writer.writeheader()
            
            # Store both file and writer
            value['file'] = file
            value['writer'] = writer
                
            

    def close_mission(self):
        if not self.raw_file:
            raise FileExistsError("Mission not initialized")

        self.raw_file.close()
        for value in self.parsed_files.values():
            if value["file"]:
                value['file'].close()
    

    def write(self, raw_packet: str, parsed_packet: ParsedTransmission | None):
        if not self.raw_file:
            raise FileExistsError("Mission not initialized")
        
        self.raw_file.write(raw_packet + "\n")
        self.raw_file.flush()


        if not parsed_packet:
            return

        for block in parsed_packet.blocks:
            block_type = type(block)
            
            # Check if the block is a key inside of the parsed_files dict
            if block_type in self.parsed_files:
                print(f"Block type: {block_type.__name__}")

                writer_entry = self.parsed_files[block_type]
                writer = writer_entry['writer']
                file = writer_entry['file']

                # Return obj of keys/values not including keys that start with '_'
                data = {k: v for k, v in vars(block).items() if not k.startswith('_')}

                if writer and file:
                    writer.writerow(data)
                    file.flush()
            else:
                print(f"Unhandled block type: {type(block).__name__}")

    def start(self):
        self.recording = True

    def stop(self):
        self.recording = False
