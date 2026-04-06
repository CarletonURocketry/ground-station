import json
import argparse
import logging
from pathlib import Path
from time import time

from ground_station_v2.radio.rn2483 import RN2483Radio as Radio
from ground_station_v2.config import RadioParameters as Parameters, Config
from ground_station_v2.radio.packets.spec import parse_rn2483_transmission
from ground_station_v2.record import Record

logger = logging.getLogger(__name__)


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
    configure_logging(script_dir / "logs" / "receive.log")

    parser = argparse.ArgumentParser(description="Receive data from RN2483 radio")
    parser.add_argument("port", help="COM port/serial port where the radio is connected")
    parser.add_argument("--save", action="store_true", help="Save received data to recordings directory and attempt parsing")
    args = parser.parse_args()

    config_path = script_dir.parent / "config.json"

    with open(config_path) as f:
        config_json = json.load(f)
        params = Parameters.from_json(config_json["radio_params"])
        config = Config.from_json(config_json)

    logger.info("Using parameters: %s", params)

    radio = Radio(args.port)
    radio.setup(params)
    logger.info("Radio configured successfully")

    recorder = None
    
    if args.save:
        recorder = Record()
        mission_name = str(time())
        recordings_path = str(script_dir.parent / "recordings")
        recorder.init_mission(recordings_path, mission_name)
        logger.info("Saving to: %s/%s", recordings_path, mission_name)

    while True:
        received = radio.receive()
        if received:
            snr = radio.signal_report()

            if args.save and recorder:
                parsed = parse_rn2483_transmission(received, config)
                recorder.write(received, parsed)

                if parsed:
                    logger.info("snr_db=%d blocks=%d", snr, len(parsed.blocks))
                    for blk in parsed.blocks:
                        cls = type(blk)
                        logger.info("  block class=%s payload_bytes=%d", cls.__name__, cls.size())
                else:
                    logger.info("snr_db=%d blocks=0 parsing failed", snr)
            else:
                text = bytes.fromhex(received).decode("ascii", errors="replace")
                logger.info("snr_db=%d message=%s", snr, text)


if __name__ == "__main__":
    main()
