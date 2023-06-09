# A Python-based ground station for collecting telemetry information from the CU-InSpace rocket.
# This data is collected using UART and is transmitted to the user interface using WebSockets.
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)

from multiprocessing import Process, Queue
from re import sub
import logging
from modules.misc.config import load_config

from modules.misc.messages import print_cu_rocket
from modules.serial.serial_manager import SerialManager
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler
from modules.misc.cli import parser

VERSION: str = "0.5.0-DEV"
STR_TO_LOGGING_MODE: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class ShutdownException(Exception):
    pass


# Get the arguments
args = vars(parser.parse_args())

# Set up logging

log_handlers: list = [logging.StreamHandler()]  # Always print to stdout
if args.get("o") is not None:
    log_handlers.append(logging.FileHandler(args.get("o", "logfile.log")))

logging.basicConfig(
    level=STR_TO_LOGGING_MODE[args.get("l", "info")],
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


def main():
    # Set up queues
    serial_status = Queue()
    ws_commands = Queue()
    serial_ws_commands = Queue()
    telemetry_ws_commands = Queue()

    radio_signal_report = Queue()
    rn2483_radio_input = Queue()
    rn2483_radio_payloads = Queue()
    telemetry_json_output = Queue()

    # Print display screen
    print_cu_rocket("No Name (Gas Propelled Launching Device)", VERSION)

    # Load config file
    config = load_config("config.json")

    # Initialize Serial process to communicate with board
    # Incoming information comes directly from RN2483 LoRa radio module over serial UART
    # Outputs information in hexadecimal payload format to rn2483_radio_payloads
    serial = Process(
        target=SerialManager,
        args=(
            serial_status,
            serial_ws_commands,
            radio_signal_report,
            rn2483_radio_input,
            rn2483_radio_payloads,
            config,
        ),
    )
    serial.start()
    logger.info(f"{'Serial':.<16} started.")

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
        ),
    )
    telemetry.start()
    logger.info(f"{'Telemetry':.<16} started.")

    # Initialize Tornado websocket for UI communication
    # This is PURELY a pass through of data for connectivity. No format conversion is done here.
    # Incoming information comes from telemetry_json_output from telemetry
    # Outputs information to connected websocket clients
    websocket = Process(target=WebSocketHandler, args=(telemetry_json_output, ws_commands), daemon=True)
    websocket.start()
    logger.info(f"{'WebSocket':.<16} started.")

    while True:
        # Messages sent to main process for handling

        # WS Commands
        while not ws_commands.empty():
            try:
                parse_ws_command(ws_commands.get(), serial_ws_commands, telemetry_ws_commands)
            except ShutdownException:
                logger.warning("Backend shutting down........")
                serial.terminate()
                telemetry.terminate()
                websocket.terminate()
                print("Good bye.")
                exit(0)


def parse_ws_command(ws_cmd: str, serial_commands: Queue, telemetry_commands: Queue) -> None:
    """Parses a websocket command and places it on the correct process queue (telemetry or serial)."""

    # Remove special characters
    parsed_command = sub(r"[^\da-zA-Z_./\s-]+", "", ws_cmd).split(" ")

    if not parsed_command:
        logger.error("WS: Error parsing command")

    match parsed_command[0].lower():
        case "serial":
            serial_commands.put(parsed_command[1:])
        case "telemetry":
            telemetry_commands.put(parsed_command[1:])
        case "shutdown":
            raise ShutdownException
        case _:
            logger.error(f"Invalid websocket command: {ws_cmd}")


if __name__ == "__main__":
    main()
