__author__ = "Angus Jull"

from pathlib import Path
import argparse
import logging

DESC: str = "Converts a logfile from the rocket (a binary file or with no line breaks) into a mission file"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LogfileIterator:
    def __init__(self, replay_path: Path):
        self.replay_path = replay_path

    def __iter__(self):
        with open(self.replay_path, "rb") as file:
            data = file.read()

        if len(data) < 9:
            return

        callsign = data[0:9]
        logger.info(f"Callsign: {callsign.hex()}")
        next = data.find(callsign, 8)
        while next != -1:
            yield data[:next].hex()
            data = data[next:]
            next = data.find(callsign, 8)
        yield data.hex()


def logfile_to_mission(logfile: Path, mission: Path) -> None:
    with open(mission, "w") as mission_file:
        for index, packet in enumerate(LogfileIterator(logfile)):
            logger.info(
                f"Callsign: {packet[:18]} Timestamp: {packet[18:22]} Blocks: {packet[22:24]} Packet Number: {packet[24:26]}"
            )
            logger.info(f"packet #{index}: {packet}")
            mission_file.write(packet + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("logfile_input", type=Path, help="The logfile to convert")
    parser.add_argument("mission_output", type=Path, help="The mission file to create")
    args = parser.parse_args()
    logfile_to_mission(args.logfile_input, args.mission_output)
