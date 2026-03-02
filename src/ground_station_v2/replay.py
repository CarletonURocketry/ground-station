from pathlib import Path
import asyncio
import logging
import csv
import time
from typing import Any, AsyncGenerator

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
            raise FileNotFoundError(f"Replay path not found: {replay_path}")
        
        self.replay_path = replay_path
        self.speed = speed
        self.playing = True
        logger.info(f"Replay started: {replay_path} at speed {speed}x")

    async def run(self) -> AsyncGenerator[tuple[float, dict[str, str], str], None]:
        if not self.replay_path or not self.playing:
            return
            
        try:
            parsed_dir = self.replay_path / "parsed"
            all_blocks: list[Any] = []
            
            for csv_file in parsed_dir.glob("*.csv"):
                with open(csv_file, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        timestamp = float(row["measurement_time"])
                        all_blocks.append((timestamp, row, csv_file.stem))
            
            all_blocks.sort(key=lambda x: x[0])
            
            if not all_blocks:
                return
            
            while self.playing:
                start_time = all_blocks[0][0]
                real_start = time.time()
                
                for timestamp, row, block_type in all_blocks:
                    if not self.playing:
                        break
                    
                    while self.speed == 0 and self.playing:
                        await asyncio.sleep(0.1)
                    
                    if not self.playing:
                        break
                    
                    mission_elapsed = timestamp - start_time
                    real_elapsed = time.time() - real_start
                    target_real_elapsed = mission_elapsed / self.speed
                    
                    wait_time = target_real_elapsed - real_elapsed
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                    
                    yield (timestamp, row, block_type)
                
                if self.playing:
                    logger.info("Replay loop complete, restarting...")
                
        except Exception as e:
            logger.error(f"Error during parsed replay: {e}", exc_info=True)
        finally:
            self.playing = False
            logger.info("Parsed replay finished")

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
