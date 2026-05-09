#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


RECORDINGS_DIR = Path(__file__).parent.parent.parent / "recordings"


def latest_recording(recordings: Path) -> Path:
    dirs = [d for d in recordings.iterdir() if d.is_dir()]
    if not dirs:
        print(f"No recordings found in {recordings}", file=sys.stderr)
        sys.exit(1)
    return max(dirs, key=lambda d: d.stat().st_mtime)


def load_csv(path: Path) -> tuple[list[float], dict[str, list[float]]]:
    times: list[float] = []
    fields: dict[str, list[float]] = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                times.append(float(row["measurement_time"]))
            except (KeyError, ValueError):
                continue
            for key, val in row.items():
                if key == "measurement_time":
                    continue
                try:
                    fields.setdefault(key, []).append(float(val))
                except (ValueError, TypeError):
                    pass

    return times, fields


SENSORS = [
    "magnetic_field",
    "linear_acceleration",
    "angular_velocity",
    "altitude_above_sea_level",
]


def plot_recording(parsed_dir: Path) -> None:
    csvs = [parsed_dir / f"{s}.csv" for s in SENSORS if (parsed_dir / f"{s}.csv").exists()]
    if not csvs:
        print(f"No CSV files found in {parsed_dir}", file=sys.stderr)
        sys.exit(1)

    fig, axs = plt.subplots(2, 2, figsize=(10, 8), squeeze=False)
    fig.suptitle(parsed_dir.parent.name)

    for i in range(len(csvs), 4):
        axs[i // 2][i % 2].set_visible(False)

    for i, csv_path in enumerate(csvs):
        ax = axs[i // 2][i % 2]
        sensor = csv_path.stem
        times, fields = load_csv(csv_path)

        if not times:
            ax.set_visible(False)
            continue

        for field, vals in fields.items():
            ax.plot(times[: len(vals)], vals, linewidth=0.8, label=field)
        ax.set_xlabel("Time (s)")
        if len(fields) > 1:
            ax.legend(loc="upper right", fontsize=7)

        ax.set_title(sensor.replace("_", " ").title())

    fig.tight_layout()
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Display telemetry graphs from a recording")
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=None,
        help="Recording directory (defaults to the latest)",
    )
    args = parser.parse_args()

    recording = args.directory if args.directory is not None else latest_recording(RECORDINGS_DIR)
    parsed_dir = recording / "parsed"

    if not parsed_dir.is_dir():
        print(f"No parsed directory found in {recording}", file=sys.stderr)
        sys.exit(1)

    plot_recording(parsed_dir)


if __name__ == "__main__":
    main()
