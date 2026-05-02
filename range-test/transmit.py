import argparse
import json
import logging
import time
from pathlib import Path

from ground_station_v2.config import RadioParameters
from ground_station_v2.radio.rn2483 import RN2483Radio

PAYLOAD_BYTES: int = 255
# a transmission delay is needed to avoid every other packet being dropped
# this is a compromise solution, a better one should be found
# the delay depends on the script, if you don't want to report the snr you can decrease it
# larger packet size means larger delay
TRANSMISSION_DELAY_SECONDS: float = 0.10
logger = logging.getLogger(__name__)

# dynamically build a fixed lenght payload
def build_fixed_payload(counter: int) -> str:
    prefix = f"VA3INI RANGE TEST #{counter} "
    filler = "X" * (PAYLOAD_BYTES - len(prefix.encode("ascii")))
    payload = prefix + filler
    return payload


def configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def main() -> None:
    script_dir = Path(__file__).parent
    configure_logging(script_dir / "logs" / "transmit.log")

    parser = argparse.ArgumentParser(description="Transmit data over RN2483 radio")
    parser.add_argument("port", help="COM port/serial port where the radio is connected")
    args = parser.parse_args()

    logger.info("Using packet length: %d", PAYLOAD_BYTES)
    logger.info("Using transmission delay: %.3fs", TRANSMISSION_DELAY_SECONDS)

    # Get config file path relative to this script
    config_path = script_dir.parent / "config.json"

    with open(config_path) as f:
        config = json.load(f)
        params = RadioParameters.from_json(config["radio_params"])

    logger.info("Using parameters: %s", params)

    # Initialize radio with port and parameters
    radio = RN2483Radio(args.port)

    # Setup the radio (reset, configure, etc.)
    radio.setup(params)
    logger.info("Radio configured successfully")

    counter = 0
    while True:
        data = build_fixed_payload(counter)
        logger.info("Transmitting: %s", data)

        if not radio.transmit(data):
            logger.error("TRANSMIT FAILED %d", counter)
        else:
            counter += 1
            time.sleep(TRANSMISSION_DELAY_SECONDS)


if __name__ == "__main__":
    main()
