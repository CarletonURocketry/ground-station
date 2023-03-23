# A Python-based ground station for collecting telemetry information from the CU-InSpace rocket.
# This data is collected using UART and is transmitted to the user interface using WebSockets.
#
# Authors:
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)

from modules.misc.messages import print_cu_rocket
from modules.serial.serial_manager import SerialManager
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler
from modules.misc.cli import parser

from multiprocessing import Process, Queue
from re import sub
import logging

serial_status = Queue()
ws_commands = Queue()
serial_ws_commands = Queue()
telemetry_ws_commands = Queue()

radio_signal_report = Queue()
rn2483_radio_input = Queue()
rn2483_radio_payloads = Queue()
telemetry_json_output = Queue()

VERSION: str = "0.4.7-DEV"
STR_TO_LOGGING_MODE: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class ShutdownException(Exception):
    pass


def main():
    # Print display screen
    print_cu_rocket("No Name (Gas Propelled Launching Device)", VERSION, "Thomas Selwyn (Devil)")

    # Get the arguments
    args = vars(parser.parse_args())


    # Set up logging
    logging.basicConfig(
        level=STR_TO_LOGGING_MODE[args.get("l")],
        filename=args.get("o"),
        format="%(levelname)s:%(asctime)s:%(message)s ",
    )

    # Initialize Serial process to communicate with board
    # Incoming information comes directly from RN2483 LoRa radio module over serial UART
    # Outputs information in hexadecimal payload format to rn2483_radio_payloads
    serial = Process(
        target=SerialManager,
        args=(
            serial_status, serial_ws_commands,
            radio_signal_report,
            rn2483_radio_input,
            rn2483_radio_payloads
        )
    )
    serial.start()
    logging.info(f"{'Serial':.<15} started.")

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
            telemetry_ws_commands
        )
    )
    telemetry.start()
    logging.info(f"{'Telemetry':.<15} started.")

    # Initialize Tornado websocket for UI communication
    # This is PURELY a pass through of data for connectivity. No format conversion is done here.
    # Incoming information comes from telemetry_json_output from telemetry
    # Outputs information to connected websocket clients
    websocket = Process(
        target=WebSocketHandler,
        args=(telemetry_json_output, ws_commands),
        daemon=True
    )
    websocket.start()
    logging.info(f"{'WebSocket':.<15} started.")

    while True:
        # WS Commands have been sent to main process for handling
        while not ws_commands.empty():
            try:
                parse_ws_command(ws_commands.get())
            except ShutdownException:
                logging.warning("Backend shutting down........")
                serial.terminate()
                telemetry.terminate()
                websocket.terminate()
                print("Good bye.")
                exit(0)


def parse_ws_command(ws_cmd: str):
    # Remove special characters
    ws_cmd = sub(r"[^0-9a-zA-Z_./\s-]+", "", ws_cmd).split(" ")

    try:
        match ws_cmd[0].lower():
            case "serial":
                serial_ws_commands.put(ws_cmd[1:])
            case "telemetry":
                telemetry_ws_commands.put(ws_cmd[1:])
            case "shutdown":
                raise ShutdownException
            case _:
                logging.error(f"WS: Invalid command. {ws_cmd}")

    except IndexError:
        logging.error("WS: Error parsing command")


if __name__ == '__main__':
    main()
