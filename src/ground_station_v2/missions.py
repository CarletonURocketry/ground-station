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
                if file_path.is_file() and file_path.suffix == ".mission":
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
    
    def get_mission_by_name(self, name: str) -> Optional[MissionInfo]:
        """
        Get a specific mission by name.
        
        Args:
            name: The mission filename (including .mission extension)
            
        Returns:
            Dictionary containing mission info or None if not found
        """
        mission_path = self.missions_path / name
        
        if mission_path.exists() and mission_path.is_file() and name.endswith('.mission'):
            return {
                "name": name,
                "path": str(mission_path)
            }
        
        return None