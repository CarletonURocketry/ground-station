"""Replays radio packets from the mission file, outputting them as replay payloads."""

import logging
from pathlib import Path
from queue import Queue
from time import time
from modules.telemetry.block import RadioBlockType

# Set up logging
logger = logging.getLogger(__name__)


# TODO: This should be adjacent to an RN2483 radio emulator that just "receives" each packet in the mission file at the
# correct mission time.
class TelemetryReplay:
    """
    This class replays telemetry data from a mission file.
    """

    def __init__(
        self,
        replay_payloads: Queue[tuple[int, int, str]],
        replay_input: Queue[str],
        replay_speed: float,
        replay_path: Path,
    ):
        super().__init__()

        # Replay buffers (Input and output)
        self.replay_payloads: Queue[tuple[int, int, str]] = replay_payloads
        self.replay_input: Queue[str] = replay_input

        # Misc replay
        self.replay_path: Path = replay_path

        # Loop data
        self.last_loop_time: int = int(time() * 1000)
        self.total_time_offset: int = 0
        self.speed: float = replay_speed

    def run(self):
        """Run the mission until completion."""

        # TODO: fix replay speed

        # Replay raw radio transmission file
        with open(self.replay_path, "r") as file:
            for line in file:
                print(line)
                if self.speed > 0:
                    replay_data = (RadioBlockType.DATA.value, 0, line)  # TODO: remove hard-coded block type
                    self.replay_payloads.put(replay_data)

                if not self.replay_input.empty():
                    self.parse_input_command(self.replay_input.get())

    def parse_input_command(self, data: str) -> None:
        cmd_list = data.split(" ")
        match cmd_list[0]:
            case "speed":
                self.speed = float(cmd_list[1])
                # Reset loop time so resuming playback doesn't skip the time it was paused
                self.last_loop_time = int(time() * 1000)
            case _:
                raise NotImplementedError(f"Replay command of {cmd_list} invalid.")
