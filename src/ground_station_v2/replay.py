from pathlib import Path
import asyncio

class Replay:
    def __init__(self, replay_path: Path, speed: float = 1.0):
        self.replay_path = replay_path
        self.speed = speed
        self.playing = False

    # simple async generator that yields packets
    # why the hell are we storing raw packets and parsing them at runtime?
    # we should instead log raw packets in one directory and timestamped parsed data in another
    # for now this will stay
    async def run(self, websocket_client):
        self.playing = True
        with open(self.replay_path, "r") as file:
            for line in file:
                if not self.playing:
                    break
                if self.speed > 0:
                    websocket_client.send_text(line.strip())
                # TODO: this is stupid, time delay should be based on the time between packets
                # not a fixed 52ms bruh moment
                await asyncio.sleep(0.052 / self.speed if self.speed > 0 else 0.052)

    def set_speed(self, speed: float):
        self.speed = speed

    def pause(self):
        self.speed = 0.0

    def resume(self, speed: float = 1.0):
        self.speed = speed

    def stop(self):
        self.playing = False

