import multiprocessing
import time
from abc import ABC

from modules.misc.messages import printCURocket
from modules.serial.serial_rn2483_radio import SerialRN2483Radio
from modules.serial.serial_test import SerialTestClass
from modules.telemetry.telemetry import Telemetry
from modules.websocket.websocket import WebSocketHandler

rn2483_radio_input = multiprocessing.Queue()
rn2483_radio_payloads = multiprocessing.Queue()
rn2483_console_input = multiprocessing.Queue()
rn2483_console_input_request = multiprocessing.Queue()
telemetry_json_output = multiprocessing.Queue()
ws_commands = multiprocessing.Queue()


class GroundStation(ABC):

    def main(self):
        debug_mode = input("Do you want to start in DEBUG Mode?")

        printCURocket("Not a missile", "Lethal", "POWERED ASCENT")
        # Initialize Serial process to communicate with board
        # Incoming information comes directly from RN2483 LoRa radio module over serial UART
        # Outputs information in hexadecimal payload format to rn2483_radio_payloads
        Serial_Test = multiprocessing.Process(target=SerialTestClass, args=(rn2483_radio_input,
                                                                            rn2483_radio_payloads, "COM1"))
        Serial_Test.daemon = True


        if debug_mode == "True" or debug_mode == "yes":
            Serial_Test.start()

        Serial_Radio = multiprocessing.Process(target=SerialRN2483Radio, args=(rn2483_radio_input,
                                                                               rn2483_radio_payloads,
                                                                               rn2483_console_input,
                                                                               rn2483_console_input_request,
                                                                               "COM1"))
        Serial_Radio.daemon = True
        Serial_Radio.start()
        print("RN2483 Radio started")

        # Initialize Telemetry to parse radio packets, keep history and to log everything
        # Incoming information comes from rn2483_radio_payloads in payload format
        # Outputs information to telemetry_json_output in friendly json for UI
        telemetry = multiprocessing.Process(target=Telemetry,
                                            args=(rn2483_radio_input, rn2483_radio_payloads,
                                                  telemetry_json_output, ws_commands))
        telemetry.daemon = True
        telemetry.start()
        print("Telemetry started")

        # Initialize Tornado websocket for UI communication
        # This is PURELY a pass through of data for connectivity. No format conversion is done here.
        # Incoming information comes from telemetry_json_output from telemetry
        # Outputs information to connected websocket clients
        websocket = multiprocessing.Process(target=WebSocketHandler, args=(ws_commands, telemetry_json_output))
        websocket.daemon = True
        websocket.start()
        print("WebSocket started")

        # If a process requests a users input, this passes that through as subprocesses cannot use input().
        while True:
            while not rn2483_console_input_request.empty():
                input_request = rn2483_console_input_request.get()
                user_input = input(f"RN2483 Radio: {input_request}\n")
                rn2483_console_input.put(user_input)


if __name__ == '__main__':
    GroundStation().main()
