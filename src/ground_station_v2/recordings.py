from pathlib import Path
from typing import List, TypedDict
import logging

logger = logging.getLogger(__name__)

# Name of the raw hex file inside each recording directory
RAW_FILENAME = "raw"


class RecordingInfo(TypedDict):
    name: str
    path: str


class Recordings:
    """List recording directories and provide paths to their raw data for replay."""

    def __init__(self, recordings_path: str = "recordings"):
        self.recordings_path = Path(recordings_path)

    def get_recordings(self) -> List[RecordingInfo]:
        """
        Get all recordings from the recordings directory.
        Each recording is a subdirectory with a 'raw' file (hex packets).
        Returns list of { name, path } where path points to the raw file for replay.
        """
        try:
            if not self.recordings_path.exists():
                logger.warning(f"Recordings directory not found: {self.recordings_path}")
                return []

            recordings: List[RecordingInfo] = []
            for child in self.recordings_path.iterdir():
                if not child.is_dir():
                    continue
                raw_path = child / RAW_FILENAME
                if not raw_path.is_file():
                    logger.debug(f"Skipping {child.name}: no 'raw' file")
                    continue
                recordings.append({
                    "name": child.name,
                    "path": str(raw_path),
                })

            # Sort by name (timestamp) descending so newest first
            recordings.sort(key=lambda x: x["name"], reverse=True)
            logger.info(f"Retrieved {len(recordings)} recordings from {self.recordings_path}")
            return recordings

        except Exception as e:
            logger.error(f"Error retrieving recordings: {e}", exc_info=True)
            raise
