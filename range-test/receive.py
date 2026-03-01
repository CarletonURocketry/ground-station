import json
import argparse
from pathlib import Path
from time import time

from ground_station_v2.radio.rn2483 import RN2483Radio as Radio
from ground_station_v2.config import RadioParameters as Parameters, Config
from ground_station_v2.radio.packets.spec import parse_rn2483_transmission
from ground_station_v2.record import Record


def main() -> None:
    parser = argparse.ArgumentParser(description="Receive data from RN2483 radio")
    parser.add_argument("port", help="COM port/serial port where the radio is connected")
    parser.add_argument("--save", action="store_true", help="Save received data to recordings directory and attempt parsing")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config.json"

    with open(config_path) as f:
        config_json = json.load(f)
        params = Parameters.from_json(config_json["radio_params"])
        config = Config.from_json(config_json)

    print(f"Using parameters: {params}")

    radio = Radio(args.port)
    radio.setup(params)
    print("Radio configured successfully")

    recorder = None
    
    if args.save:
        recorder = Record()
        mission_name = str(time())
        recordings_path = str(script_dir.parent / "recordings")
        recorder.init_mission(recordings_path, mission_name)
        print(f"Saving to: {recordings_path}/{mission_name}")

    while True:
        received = radio.receive()
        if received:
            print(f"Received: {received}")
            print(f"SNR: {radio.signal_report()}")
            
            if args.save and recorder:
                parsed = parse_rn2483_transmission(received, config)
                recorder.write(received, parsed)
                
                if parsed:
                    print(f"Parsed: {parsed.packet_header}")
                    print(f"Blocks: {len(parsed.blocks)}")
                else:
                    print("Parsing failed")


if __name__ == "__main__":
    main()
