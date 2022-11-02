# A Python-based ground station for collecting telemetry information from the CU-InSpace rocket.
# This data is collected using UART and is transmitted to the user interface using WebSockets.
#
# Authors:
# Thomas Selwyn (Devil)

from multiprocessing import Process, Queue, Value
from multiprocessing.shared_memory import ShareableList

from modules.misc.messages import printCURocket
from modules.serial.serial_manager import SerialManager
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler

from re import sub

rn2483_radio_input = Queue()
rn2483_radio_payloads = Queue()
telemetry_json_output = Queue()

ws_commands = Queue()
serial_ws_commands = Queue()
telemetry_ws_commands = Queue()

serial_connected = Value('i', 0)
serial_connected_port = ShareableList([""])
serial_ports = ShareableList([""] * 8)


def main():
    printCURocket("Not a missile", "Lethal", "POWERED ASCENT")

    # Initialize Serial process to communicate with board
    # Incoming information comes directly from RN2483 LoRa radio module over serial UART
    # Outputs information in hexadecimal payload format to rn2483_radio_payloads
    serial_manager = Process(target=SerialManager,
                             args=(serial_connected, serial_connected_port, serial_ports,
                                   serial_ws_commands, rn2483_radio_input, rn2483_radio_payloads))
    serial_manager.start()
    print("Serial Manager started")

    # Initialize Telemetry to parse radio packets, keep history and to log everything
    # Incoming information comes from rn2483_radio_payloads in payload format
    # Outputs information to telemetry_json_output in friendly json for UI
    telemetry = Process(target=Telemetry,
                        args=(serial_connected, serial_connected_port, serial_ports,
                              rn2483_radio_payloads, telemetry_json_output, telemetry_ws_commands), daemon=True)
    telemetry.start()
    print("Telemetry started")

    # Initialize Tornado websocket for UI communication
    # This is PURELY a pass through of data for connectivity. No format conversion is done here.
    # Incoming information comes from telemetry_json_output from telemetry
    # Outputs information to connected websocket clients
    websocket = Process(target=WebSocketHandler, args=(telemetry_json_output, ws_commands), daemon=True)
    websocket.start()
    print("WebSocket started")

    while True:
        # WS Commands get sent to main process for handling to distribute to which process should handle it.
        while not ws_commands.empty():
            parse_ws_command(ws_commands.get())


def parse_ws_command(ws_cmd: str):
    # Remove special characters
    ws_cmd = sub(r"[^0-9a-zA-Z_\s]+", "", ws_cmd).split(" ")

    try:
        # WebSocket Command Aliases
        if ws_cmd[0] == "connect" or ws_cmd[0] == "disconnect":
            ws_cmd = ["serial", "rn2483_radio"] + ws_cmd
        elif ws_cmd[0] == "update":
            ws_cmd = ["telemetry"] + ws_cmd

        match ws_cmd[0]:
            case "serial":
                serial_ws_commands.put(ws_cmd)
            case "telemetry":
                telemetry_ws_commands.put(ws_cmd)
            case _:
                print("WS: Invalid command type")

    except IndexError:
        print("WS: Error parsing command")


if __name__ == '__main__':
    main()
