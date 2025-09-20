__author__ = "Jia Lin", "Angus Jull"

import sys
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import argparse
from modules.misc.config import load_config
from modules.telemetry.packet_spec import *
from modules.telemetry.parsing_utils import *
from modules.telemetry.data import *
import pandas as pd

DESC: str = "Converts a mission file to a CSV file"

def mission_to_csv(mission: Path, csv: Path, config: Config) -> None:
    data = default_telemetry_dict(0)

    with open(mission, "r") as mission_file:
        for line in mission_file:
            parsed = parse_rn2483_transmission(line, config)
            if parsed is not None:
                for block in parsed.blocks:
                    block.output_formatted(data)
    for key in data:
        if key == "last_mission_time": # this one causes errors, i don't know what it is either
            continue
        df = pd.DataFrame.from_dict(data[key], orient="index")
        df = df.transpose() # this fixes an error about array lengths not matching
        df.to_csv(f"{csv}/{key}.csv", index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("mission_input", type=Path, help="The mission file to convert")
    parser.add_argument("csv_output", type=Path, help="Folder to save CSV files to")
    args = parser.parse_args()
    config = load_config("config.json")
    mission_to_csv(args.mission_input, args.csv_output, config)