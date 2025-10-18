import sys
import json
import time
from pathlib import Path

from ground_station.misc.config import RadioParameters
from ground_station.serial.rn2483_radio import RN2483Radio

TRANSMIT_DATA: str = (
    "VA3INI - This is a test message to test the functionality of the RN2483 transceiver with a long packet containing plenty of data - VA3INI - Packet number follows"
)


def main() -> None:

    if len(sys.argv) != 2:
        print("Must provide the COM port/serial port where the radio is connected.")
        exit(1)

    print(f"Using packet length: {len(TRANSMIT_DATA.encode('ascii'))}")

    # Get config file path relative to this script
    config_path = Path(__file__).parent.parent / "src" / "config.json"
    with open(config_path) as f:
        params = RadioParameters.from_json(json.load(f))
    
    print(f"Using parameters: {params}")
    
    # Initialize radio with port and parameters
    radio = RN2483Radio(sys.argv[1], params)
    
    # Setup the radio (reset, configure, etc.)
    radio.setup(params)
    print("Radio configured successfully")

    counter = 0
    while True:
        data = f"{TRANSMIT_DATA} - #{counter}"
        print(f"Transmitting: {data}")

        start = time.time()
        if not radio.transmit(data):
            print(f"TRANSMIT FAILED {counter}")
        else:
            end = time.time()
            print(f"Period: {end - start}")
            counter += 1


if __name__ == "__main__":
    main()