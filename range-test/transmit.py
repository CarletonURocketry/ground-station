import argparse
import csv
import json
import logging
import struct
import time
from pathlib import Path

from ground_station_v2.config import RadioParameters
from ground_station_v2.radio.packets.headers import BlockType, CALLSIGN_LENGTH
from ground_station_v2.radio.packets.spec import create_fake_packet
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


ROW_INTERVAL_MS: int = 1000  # simulated time step per CSV row; flight-sim TX spacing matches this


def build_flight_sim_packet(row_index: int, lon: float, lat: float, alt_m: float) -> str:
    elapsed_ms = row_index * ROW_INTERVAL_MS
    pkt_timestamp = elapsed_ms // 30_000   # half-minutes elapsed
    measurement_time = elapsed_ms % 30_000  # ms within current half-minute

    callsign = "VA3ZAJ".ljust(CALLSIGN_LENGTH, "\x00")
    header = callsign.encode("ascii") + struct.pack("<HBB", pkt_timestamp, 2, row_index & 0xFF)

    lat_ud = int(lat * 10_000_000)
    lon_ud = int(lon * 10_000_000)
    alt_mm = int(alt_m * 1000)

    blocks = b""
    blocks += struct.pack("<BB", BlockType.COORDINATES, 1)
    blocks += struct.pack("<hii", measurement_time, lat_ud, lon_ud)
    blocks += struct.pack("<BB", BlockType.ALTITUDE_ABOVE_SEA_LEVEL, 1)
    blocks += struct.pack("<hi", measurement_time, alt_mm)

    return (header + blocks).hex()


def flight_sim(radio: RN2483Radio, csv_path: Path) -> None:
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    logger.info("Starting flight sim: %d rows every %.1fs, looping indefinitely", len(rows), ROW_INTERVAL_MS / 1000.0)
    row_index = 0
    while True:
        for row in rows:
            lat = float(row["lat"])
            lon = float(row["long"])
            alt_m = float(row["alt"])
            data = build_flight_sim_packet(row_index, lon, lat, alt_m)
            logger.info(
                "Flight sim row #%d  lat=%.6f lon=%.6f alt=%.1fm MSL",
                row_index,
                lat,
                lon,
                alt_m,
            )
            if not radio.transmit_hex(data):
                logger.error("TRANSMIT FAILED row #%d", row_index)
            else:
                row_index += 1
                time.sleep(ROW_INTERVAL_MS / 1000.0)


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
    parser.add_argument("--simulate", action="store_true", help="Transmit simulated telemetry packets in a loop instead of the fixed-length range-test payload")
    parser.add_argument("--flight-sim", action="store_true", help="Replay el_blasto.csv flight data")
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

    if args.flight_sim:
        flight_sim(radio, script_dir / "el_blasto.csv")
        return

    counter = 0
    while True:
        if args.simulate:
            data = create_fake_packet(counter)
            logger.info("Transmitting simulated packet #%d", counter)
            success = radio.transmit_hex(data)
        else:
            data = build_fixed_payload(counter)
            logger.info("Transmitting: %s", data)
            success = radio.transmit(data)

        if not success:
            logger.error("TRANSMIT FAILED %d", counter)
        else:
            counter += 1
            time.sleep(TRANSMISSION_DELAY_SECONDS)


if __name__ == "__main__":
    main()
