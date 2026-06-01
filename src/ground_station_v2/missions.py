import os
from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict
import logging

logger = logging.getLogger(__name__)


class MissionInfo(TypedDict):
    name: str
    path: str


class Mission:
    def __init__(self):
        self.missions_path = Path("missions")
    
    def get_missions(self) -> List[MissionInfo]:
        """
        Get all mission files from the missions directory.
        
        Returns:
            List of dictionaries containing mission name and path
        """
        try:
            if not self.missions_path.exists():
                logger.warning(f"Missions directory not found: {self.missions_path}")
                return []
            
            missions: List[MissionInfo] = []
            for file_path in self.missions_path.iterdir():
                if file_path.is_file():
                    missions.append({
                        "name": file_path.name,
                        "path": str(file_path)
                    })
            
            # Sort missions alphabetically by name
            missions.sort(key=lambda x: x["name"])
            logger.info(f"Retrieved {len(missions)} missions from {self.missions_path}")
            return missions
            
        except Exception as e:
            logger.error(f"Error retrieving missions: {e}", exc_info=True)
            raise
    