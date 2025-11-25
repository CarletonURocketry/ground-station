import logging
from datetime import datetime
from pathlib import Path

from src.ground_station_v2.api import run_server

Path("logs").mkdir(exist_ok=True)

log_file = f"logs/ground_station_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file),
    ],
)

if __name__ == "__main__":
    run_server()

