import sys
import json
from pathlib import Path

from ground_station.serial.rn2483_radio import RN2483Radio as Radio
from ground_station.misc.config import RadioParameters as Parameters


def main() -> None:

    if len(sys.argv) != 2:
        print("Must provide the COM port/serial port where the radio is connected.")
        exit(1)

    script_dir = Path(__file__).parent
    config_path = script_dir / "config_lora.json"
    
    with open(config_path) as f:
        config = json.load(f)
        params = Parameters.from_json(config["radio_params"])
    
    print(f"Using parameters: {params}")
    
    # Initialize radio with port and parameters
    radio = Radio(sys.argv[1])
    
    
    # Setup the radio (reset, configure, etc.)
    radio.setup(params)
    print("Radio configured successfully")

    while True:
        received = radio.receive()
        print(f"Received: {received}")
        print(f"SNR: {radio.signal_report()}")


if __name__ == "__main__":
    main()