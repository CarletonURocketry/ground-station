from pathlib import Path

# saves data in the "recordings" dir
# recording dir has child dirs for each mission, the default name is the timestamp but it should have the ability to be renamed
# each child dir has a raw and a parsed version of the incoming radio data
# the raw data should be in hex format
# the parsed data should be a collection of csvs, one for each sensor type
# the recoding class is a singleton, which means it can only be instantiated once
# it's methods are async, which means we don't need threads or processes, just one asyncio task

# Add a variable if currently recording or not, and implement start/stop. Then inside of main api when the record api request comes in, set to true and then it starts recording
class Record:
    _instance = None
    recording = False

    # singleton pattern
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # create the recordings directory if it doesn't exist
            Path("recordings").mkdir(exist_ok=True)
        return cls._instance
    
    # def write_recording(raw_packet, parsed_packet, self):
    #     # Writes recording based off

    def start(self):
        self.recording = True
        pass
    def stop(self):
        self.recording = False
        pass