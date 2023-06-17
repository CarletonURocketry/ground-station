# CLI tool commands
__author__ = "Matteo Golin"

# Imports
import argparse
import os

# Constants
DESC: str = "Select some starting parameters for the telemetry server."


# Custom types
def file_path(path: str):
    """Verifies that the argument is a valid file path."""

    if os.path.isfile(path) or os.access(os.path.dirname(path), os.W_OK):
        return path
    else:
        raise FileNotFoundError(f"{path} is not a valid file path.")


# Arguments
parser = argparse.ArgumentParser(description=DESC)

_ = parser.add_argument(
    "-l",
    help="Selects the logging level for messages in the console.",
    choices=["debug", "info", "warning", "error", "critical"],
    default="info",
)

_ = parser.add_argument(
    "-o",
    help="Output file for logging messages. Logs to console by default.",
    type=file_path,
)
