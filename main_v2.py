import argparse
import logging
from datetime import datetime
from pathlib import Path

from ground_station_v2.api import run_server

Path("logs").mkdir(exist_ok=True)

log_file = f"logs/ground_station_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file),
    ],
)

parser = argparse.ArgumentParser(description="CUInSpace Ground Station telemetry server.")
_ = parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to (default: 0.0.0.0)")
_ = parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
_ = parser.add_argument(
    "--from-recording",
    type=Path,
    metavar="RAW_FILE",
    help="Path to a raw recording file to feed into the stream at 0.6s intervals instead of reading from radio",
)

if __name__ == "__main__":
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, from_recording=args.from_recording)
