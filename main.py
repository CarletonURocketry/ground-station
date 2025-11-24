"""
A Python-based ground station for collecting telemetry information from the CU-InSpace rocket.
This data is collected using UART and is transmitted to the user interface using WebSockets.
"""

import multiprocessing as mp
from multiprocessing import Process
from queue import Queue
from re import sub
import logging
from typing import TypeAlias, Any
import json

from ground_station.misc.config import Config
from ground_station.misc.messages import print_cu_rocket
from ground_station.serial.serial_manager import SerialManager
from ground_station.telemetry.telemetry import Telemetry
from ground_station.websocket.websocket import WebSocketHandler
from ground_station.misc.cli import parser

JSON: TypeAlias = dict[str, Any]
STR_TO_LOGGING_MODE: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# Constants
VERSION: str = "2.0.0-DEV"


class ShutdownException(Exception):
    pass


# Get the arguments
args = vars(parser.parse_args())

# Set up logging
log_handlers: list[logging.Handler] = [logging.StreamHandler()]  # Always print to stdout
if args.get("o") is not None:
    log_handlers.append(logging.FileHandler(args.get("o", "logfile.log")))

logging.basicConfig(
    level=STR_TO_LOGGING_MODE[args.get("l", "info")],
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


def main():
    # Set up queues
    serial_status: Queue[str] = mp.Queue()  # type: ignore
    ws_commands: Queue[str] = mp.Queue()  # type: ignore
    serial_ws_commands: Queue[list[str]] = mp.Queue()  # type: ignore
    telemetry_ws_commands: Queue[list[str]] = mp.Queue()  # type: ignore

    radio_signal_report: Queue[int] = mp.Queue()  # type: ignore
    rn2483_radio_input: Queue[str] = mp.Queue()  # type: ignore
    rn2483_radio_payloads: Queue[str] = mp.Queue()  # type: ignore
    telemetry_json_output: Queue[JSON] = mp.Queue()  # type: ignore

    # Load config file
    config = Config.from_json(json.load(open("config.json")))

    # Print display screen
    print_cu_rocket(config.rocket_name, VERSION)

    # Initialize Serial process to communicate with board
    # Incoming information comes directly from RN2483 LoRa radio module over serial UART
    # Outputs information in hexadecimal payload format to rn2483_radio_payloads
    serial = Process(
        target=SerialManager(
            serial_status,
            serial_ws_commands,
            radio_signal_report,
            rn2483_radio_input,
            rn2483_radio_payloads,
            config,
        ).run,
    )
    serial.start()
    logger.info(f"{'Serial':.<13} started.")

    # Initialize Telemetry to parse radio packets, keep history and to log everything
    # Incoming information comes from rn2483_radio_payloads in payload format
    # Outputs information to telemetry_json_output in friendly json for UI
    telemetry = Process(
        target=Telemetry,
        args=(
            serial_status,
            rn2483_radio_payloads,
            rn2483_radio_input,
            radio_signal_report,
            telemetry_json_output,
            telemetry_ws_commands,
            config,
            VERSION,
        ),
    )
    telemetry.start()
    logger.info(f"{'Telemetry':.<13} started.")

    # Initialize Tornado websocket for UI communication
    # This is PURELY a pass through of data for connectivity. No format conversion is done here.
    # Incoming information comes from telemetry_json_output from telemetry
    # Outputs information to connected websocket clients
    websocket = Process(target=WebSocketHandler, args=(telemetry_json_output, ws_commands), daemon=True)
    websocket.start()
    logger.info(f"{'WebSocket':.<13} started.")

    while True:
        # Messages sent to main process for handling
        try:
            # WS Commands
            command = ws_commands.get()
            parse_ws_command(command, serial_ws_commands, telemetry_ws_commands)
        except ShutdownException:
            logger.info("Ground Station shutting down...")
            serial.terminate()
            telemetry.terminate()
            websocket.terminate()
            logger.info("Ground Station shutdown.")
            exit(0)


def parse_ws_command(ws_cmd: str, serial_commands: Queue[list[str]], telemetry_commands: Queue[list[str]]) -> None:
    """Parses a websocket command and places it on the correct process queue (telemetry or serial)."""

    # If the client id exists, then parse it out
    # Example format with a client id: "__client_id__7ecc8f4e telemetry replay play july_12th"
    client_id = ""
    if ws_cmd.startswith("__client_id__"):
        parts = ws_cmd.split(" ", 1)
        client_id = parts[0].replace("__client_id__", "")
        ws_cmd = parts[1] if len(parts) > 1 else ""

    # Remove special characters
    parsed_command = sub(r"[^\da-zA-Z_./\s-]+", "", ws_cmd).split(" ")

    if not parsed_command:
        logger.error("WS: Error parsing command")

    match parsed_command[0].lower():
        case "serial":
            serial_commands.put(parsed_command[1:])
        case "telemetry":
            # Include client id as the first element for telemetry commands
            # This is so it can send specific data to specific clients (replay data, anything else we want to add in the future)
            telemetry_commands.put([client_id] + parsed_command[1:])
        case "shutdown":
            raise ShutdownException
        case _:
            logger.error(f"Invalid websocket command: {ws_cmd}")


if __name__ == "__main__":
    main()
