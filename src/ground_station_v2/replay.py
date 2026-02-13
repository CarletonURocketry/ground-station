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
        self.current_line: int = 0
        self.total_lines: int = 0
        self.lines: list[str] = []  # Pre-loaded lines for random access

    def start(self, replay_path: Path | str, speed: float = 1.0):
        if isinstance(replay_path, str):
            replay_path = Path(replay_path)
        
        if not replay_path.exists():
            raise FileNotFoundError(f"Replay file not found: {replay_path}")
        
        self.replay_path = replay_path
        self.speed = speed
        self.playing = True
        self.current_line = 0
        
        # Pre-load all lines for position tracking and future seeking
        with open(replay_path, "r") as file:
            self.lines = [line.strip() for line in file if line.strip()]
        self.total_lines = len(self.lines)
        
        logger.info(f"Replay started: {replay_path} at speed {speed}x ({self.total_lines} packets)")

    # simple async generator that yields packets
    # Now uses pre-loaded lines for position tracking
    async def run(self):
        if not self.replay_path or not self.playing or not self.lines:
            return
        
        try:
            while self.current_line < self.total_lines and self.playing:
                # Wait while paused (speed == 0)
                while self.speed == 0 and self.playing:
                    await asyncio.sleep(0.1)
                
                if not self.playing:
                    break
                
                line = self.lines[self.current_line]
                self.current_line += 1
                
                yield line
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
        self.current_line = 0
        self.lines = []
        self.total_lines = 0
        logger.info("Replay stopped")
    
    def is_playing(self) -> bool:
        return self.playing
    
    def get_status(self) -> dict:
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
        logger.info(f"Seeked to line {line_number}/{self.total_lines}")
