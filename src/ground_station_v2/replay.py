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
        self.current_line: int = 0
        self.total_lines: int = 0
        self.blocks: list[Any] = []

    def start(self, replay_path: Path | str, speed: float = 1.0):
        if isinstance(replay_path, str):
            replay_path = Path(replay_path)
        
        if not replay_path.exists():
            raise FileNotFoundError(f"Replay path not found: {replay_path}")
        
        self.replay_path = replay_path
        self.speed = speed
        self.playing = True
        self.current_line = 0
        
        blocks: list[Any] = []
        for csv_file in (replay_path / "parsed").glob("*.csv"):
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    blocks.append((float(row["measurement_time"]), row, csv_file.stem))

        blocks.sort(key=lambda x: x[0])
        self.blocks = blocks
        self.total_lines = len(blocks)
        
        logger.info(f"Replay started: {replay_path} at speed {speed}x ({self.total_lines} packets)")

    async def run(self) -> AsyncGenerator[tuple[float, dict[str, str], str], None]:
        if not self.replay_path or not self.playing or not self.blocks:
            return
            
        try:
            while self.playing:
                start_time = self.blocks[self.current_line][0]
                real_start = time.time()

                while self.current_line < self.total_lines and self.playing:
                    line = self.current_line

                    while self.speed == 0 and self.playing:
                        await asyncio.sleep(0.1)

                    if not self.playing:
                        break

                    if self.current_line != line:
                        start_time = self.blocks[self.current_line][0]
                        real_start = time.time()
                        continue

                    timestamp, row, block_type = self.blocks[line]
                    mission_elapsed = timestamp - start_time
                    real_elapsed = time.time() - real_start
                    wait_time = (mission_elapsed / self.speed) - real_elapsed
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                    if self.current_line != line:
                        start_time = self.blocks[self.current_line][0]
                        real_start = time.time()
                        continue

                    yield (timestamp, row, block_type)
                    self.current_line += 1

                if self.playing:
                    logger.info("Replay loop complete, restarting...")
                    self.current_line = 0
                
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
        self.current_line = 0
        self.blocks = []
        self.total_lines = 0
        logger.info("Replay stopped")
    
    def is_playing(self) -> bool:
        return self.playing
    
    def get_status(self) -> dict[str, object]:
        """Return current replay status for API endpoint."""
        return {
            "is_playing": self.playing,
            "is_paused": self.speed == 0 and self.playing,
            "current_line": self.current_line,
            "total_lines": self.total_lines,
            "progress": self.current_line / self.total_lines if self.total_lines > 0 else 0,
            "speed": self.speed,
            "replay_path": str(self.replay_path) if self.replay_path else None,
        }
    
    def seek(self, line_number: int):
        """Seek to a specific line number (0-indexed)."""
        if line_number < 0:
            line_number = 0
        if line_number >= self.total_lines:
            line_number = self.total_lines - 1 if self.total_lines > 0 else 0
        
        self.current_line = line_number
