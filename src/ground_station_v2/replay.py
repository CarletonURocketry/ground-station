from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)


class Replay:
    def __init__(self):
        self.replay_path: Path | None = None
        self.speed: float = 1.0
        self.playing: bool = False
        self.task: asyncio.Task | None = None

    def start(self, replay_path: Path | str, speed: float = 1.0):
        if isinstance(replay_path, str):
            replay_path = Path(replay_path)
        
        if not replay_path.exists():
            raise FileNotFoundError(f"Replay file not found: {replay_path}")
        
        self.replay_path = replay_path
        self.speed = speed
        self.playing = True
        logger.info(f"Replay started: {replay_path} at speed {speed}x")

    # simple async generator that yields packets
    # why the hell are we storing raw packets and parsing them at runtime?
    # we should instead log raw packets in one directory and timestamped parsed data in another
    # for now this will stay
    async def run(self):
        if not self.replay_path or not self.playing:
            return
        
        try:
            with open(self.replay_path, "r") as file:
                for line in file:
                    if not self.playing:
                        break
                    
                    # Wait while paused (speed == 0)
                    while self.speed == 0 and self.playing:
                        await asyncio.sleep(0.1)
                    
                    if not self.playing:
                        break
                    
                    yield line.strip()
                    # TODO: this is stupid, time delay should be based on the time between packets
                    # not a fixed 52ms bruh moment
                    await asyncio.sleep(0.052 / self.speed if self.speed > 0 else 0.052)
        except Exception as e:
            logger.error(f"Error during replay: {e}", exc_info=True)
        finally:
            self.playing = False
            logger.info("Replay finished")

    def set_speed(self, speed: float):
        self.speed = speed
        logger.info(f"Replay speed set to {speed}x")

    def pause(self):
        self.speed = 0.0
        logger.info("Replay paused")

    def resume(self, speed: float = 1.0):
        self.speed = speed
        logger.info(f"Replay resumed at {speed}x")

    def stop(self):
        self.playing = False
        logger.info("Replay stopped")
    
    def is_playing(self) -> bool:
        return self.playing
